import json
import re

from .llm import ask_llm

VALID_TOOLS = {"rag", "time", "calculator", "web_search"}
GREETING_RESPONSES = {
    "hi": "Hi! How can I help you today?",
    "hello": "Hello! How can I help you today?",
    "hey": "Hey! What can I help you with?",
    "good morning": "Good morning! How can I help you today?",
    "good afternoon": "Good afternoon! How can I help you today?",
    "good evening": "Good evening! How can I help you today?",
}


def greeting_response(question: str) -> str | None:
    normalized_question = " ".join(question.lower().strip().split())
    greeting = normalized_question.rstrip("!.?,")
    return GREETING_RESPONSES.get(greeting)


def select_tool(
    question: str,
    conversation_history: str = "",
) -> str:
    if greeting_response(question):
        return "greeting"

    normalized_question = question.lower()
    if any(word in normalized_question for word in ("what time", "current time", "today's date", "what date", "what day")):
        return "time"

    web_search_markers = (
        "search the web",
        "search online",
        "look up online",
        "on the internet",
        "latest news",
        "current news",
        "recent news",
        "web search",
        "online sources",
        "latest information",
        "as of today",
        "current price",
        "current status",
        "current population",
        "recently",
    )
    if any(marker in normalized_question for marker in web_search_markers) or (
        "current " in normalized_question and "current time" not in normalized_question
    ):
        return "web_search"

    if any(symbol in normalized_question for symbol in ("+", "-", "*", "/", "%")) or any(
        word in normalized_question for word in ("calculate", "plus", "minus", "times", "divided")
    ):
        return "calculator"

    prompt = f"""
You select one tool for an enterprise assistant.

Tools:
- "time": current date, day, time, or timezone questions.
- "calculator": arithmetic or mathematical calculations.
- "web_search": current events, recent facts, online research, or questions
  that explicitly require web sources.
- "rag": company policies, employee documents, travel policies,
  or any question not covered by the other tools.

Conversation history:
{conversation_history}

Return only valid JSON:

{{"tool": "rag"}}

Current question:
{question}
"""

    try:
        response = ask_llm(prompt, temperature=0)

        response = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.strip(),
            flags=re.IGNORECASE,
        )

        tool = json.loads(response).get("tool", "rag").lower()

        return tool if tool in VALID_TOOLS else "rag"

    except Exception:
        return "rag"
