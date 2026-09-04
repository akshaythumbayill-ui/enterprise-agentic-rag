import os
import logging

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger("enterprise_agent")

# CURRENT ACTIVE Groq models (updated 2025)
# These are the models that should work with an active account
AVAILABLE_MODELS = [
    "openai/gpt-oss-20b",
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
        
        # Fallback: try the most commonly available model
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return {"status": "valid", "model_used": "openai/gpt-oss-20b"}
        except Exception as e:
            logger.warning(f"Model openai/gpt-oss-20b failed: {e}")
        
        return {"status": "invalid", "error": "No available models found with this API key"}
        
    except Exception as e:
        return {"status": "invalid", "error": str(e)}


def ask_llm(prompt: str, temperature: float = 0.2) -> str:
    client = get_client()
    
    # Get preferred model from .env, or use list
    preferred_model = os.getenv("GROQ_MODEL", "")
    models_to_try = [preferred_model] + [m for m in AVAILABLE_MODELS if m != preferred_model] if preferred_model else AVAILABLE_MODELS
    
    last_error = None
    
    for model in models_to_try:
        if not model:
            continue
            
        try:
            logger.info(f"Attempting to use model: {model}")
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional enterprise knowledge-base assistant. "
                            "Give concise, accurate answers."
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