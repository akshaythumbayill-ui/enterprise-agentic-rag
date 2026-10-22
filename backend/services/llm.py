import os
import logging

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger("enterprise_agent")

# CURRENT ACTIVE Groq models (updated 2025)
# These are the models that should work with an active account
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.3-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    return Groq(api_key=api_key)


def test_api_key():
    """Test if the Groq API key is valid and has access to models."""
    try:
        client = get_client()
        
        # Try to list available models first
        try:
            models = client.models.list()
            available_model_ids = [model.id for model in models.data]
            logger.info(f"Available models: {available_model_ids}")
            
            # Try the first available model
            if available_model_ids:
                test_model = available_model_ids[0]
                response = client.chat.completions.create(
                    model=test_model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10,
                )
                return {"status": "valid", "model_used": test_model, "available_models": available_model_ids}
        except Exception as e:
            logger.warning(f"Could not list models: {e}")
        
        # Fallback: try versatile models
        for model in AVAILABLE_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10,
                )
                return {"status": "valid", "model_used": model}
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        return {"status": "invalid", "error": "No available models found with this API key"}
        
    except Exception as e:
        return {"status": "invalid", "error": str(e)}


def ask_llm(prompt: str, temperature: float = 0.1, max_tokens: int = 2048) -> str:
    """
    Query the LLM with the given prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        temperature: Sampling temperature (0.0-1.0). Lower for factual RAG, higher for creative.
        max_tokens: Maximum tokens in the response
    
    Returns:
        The LLM's response text
    """
    client = get_client()
    
    # Get preferred model from .env, or use list
    preferred_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    models_to_try = [preferred_model] + [m for m in AVAILABLE_MODELS if m != preferred_model] if preferred_model else AVAILABLE_MODELS
    
    last_error = None
    
    for model in models_to_try:
        if not model:
            continue
            
        try:
            logger.info(f"Attempting to use model: {model} with temperature {temperature}")
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional enterprise knowledge-base assistant. "
                            "Your role is to provide accurate, well-structured answers based on the provided document context. "
                            "Be thorough but concise. "
                            "When you find information in the documents, cite the specific details clearly. "
                            "If information is not found in the documents, state that clearly rather than guessing. "
                            "Organize your answers with clear headings and bullet points when appropriate."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            logger.info(f"Successfully used model: {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Model {model} failed: {last_error}")
            continue
    
    # If all models fail, raise the last error
    raise RuntimeError(
        f"❌ GROQ API ERROR: Your API key doesn't have access to any models. "
        f"All models are decommissioned or unavailable. "
        f"\n\n🔧 SOLUTION:\n"
        f"1. Visit https://console.groq.com/keys\n"
        f"2. Create a NEW API key (delete the old one)\n"
        f"3. Paste the new key in your .env file\n"
        f"4. Restart the backend\n\n"
        f"Last error: {last_error}"
    )