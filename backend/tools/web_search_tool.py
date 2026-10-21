import logging
import os
import re
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("enterprise_agent")

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class WebSearchTool:
    """Search the public web through Tavily or DuckDuckGo and return grounded source records."""

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def run(
        self,
        question: str,
        max_results: int | None = None,
        conversation_history: str = "",
    ) -> Dict[str, Any]:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        provider = os.getenv("WEB_SEARCH_PROVIDER", "auto").strip().lower()

        configured_results = os.getenv("TAVILY_MAX_RESULTS", "5")
        try:
            result_count = max_results or int(configured_results)
        except ValueError:
            result_count = 5
        result_count = min(max(result_count, 1), 10)

        search_query = self._normalise_query(question, conversation_history)

        # Explicit DuckDuckGo provider
        if provider in ("duckduckgo", "ddg"):
            return self._run_duckduckgo(question, search_query, result_count)

        # Missing Tavily key handling
        if not api_key:
            return {
                "tool": "web_search",
                "answer": (
                    "Web search is not configured. Add TAVILY_API_KEY to the "
                    ".env file and restart the backend."
                ),
                "sources": [],
                "error": "TAVILY_API_KEY is missing",
                "grounded": False,
            }

        payload = {
            "api_key": api_key,
            "query": search_query,
            "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "advanced"),
            "max_results": result_count,
            "include_answer": "advanced",
            "include_raw_content": False,
        }

        try:
            response = self.session.post(
                TAVILY_SEARCH_URL,
                json=payload,
                timeout=float(os.getenv("TAVILY_TIMEOUT_SECONDS", "15")),
            )
            response.raise_for_status()
            data = response.json()
        except (requests.Timeout, requests.RequestException, ValueError) as error:
            logger.warning(
                "Tavily search failed (%s). Falling back to DuckDuckGo search.",
                error,
            )
            ddg_result = self._run_duckduckgo(question, search_query, result_count)
            if ddg_result.get("grounded"):
                return ddg_result
            return self._error("Web search is temporarily unavailable.", str(error))

        sources = self._normalise_sources(data.get("results", []))
        answer = (data.get("answer") or "").strip()
        if self._is_python_release_question(question):
            authoritative_answer = self._python_release_answer(sources)
            if authoritative_answer:
                answer = authoritative_answer
                sources = self._official_python_sources(sources)
        if not answer:
            answer = self._synthesize_answer(question, sources)

        return {
            "tool": "web_search",
            "question": question,
            "search_query": search_query,
            "answer": answer or "No relevant web results were found.",
            "sources": sources,
            "grounded": bool(sources),
        }

    def _run_duckduckgo(
        self,
        question: str,
        search_query: str,
        result_count: int,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        try:
            try:
                from ddgs import DDGS
                ddgs_client = DDGS()
                raw_results = list(ddgs_client.text(search_query, max_results=result_count))
            except ImportError:
                from duckduckgo_search import DDGS
                ddgs_client = DDGS()
                raw_results = list(ddgs_client.text(search_query, max_results=result_count))

            for item in raw_results:
                results.append({
                    "title": item.get("title", "Untitled source"),
                    "url": item.get("href", ""),
                    "content": item.get("body", ""),
                    "score": None,
                })
        except Exception as error:
            logger.warning("DuckDuckGo ddgs API error: %s. Attempting DuckDuckGo HTML fallback.", error)
            try:
                from bs4 import BeautifulSoup
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                resp = self.session.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": search_query},
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for result in soup.select(".result")[:result_count]:
                        link_el = result.select_one(".result__title .result__url, .result__title a")
                        title_el = result.select_one(".result__title")
                        snippet_el = result.select_one(".result__snippet")
                        url = link_el.get("href", "").strip() if link_el else ""
                        title = title_el.get_text(strip=True) if title_el else "Web Source"
                        content = snippet_el.get_text(strip=True) if snippet_el else ""
                        if url and not url.startswith("/"):
                            results.append({
                                "title": title,
                                "url": url,
                                "content": content,
                                "score": None,
                            })
            except Exception as html_err:
                logger.error("DuckDuckGo HTML fallback error: %s", html_err)

        if not results:
            return self._error("Web search is temporarily unavailable.", "No web search providers succeeded.")

        sources = self._normalise_sources(results)
        if self._is_python_release_question(question):
            authoritative_answer = self._python_release_answer(sources)
            if authoritative_answer:
                return {
                    "tool": "web_search",
                    "question": question,
                    "search_query": search_query,
                    "answer": authoritative_answer,
                    "sources": self._official_python_sources(sources),
                    "grounded": bool(sources),
                }

        answer = self._synthesize_answer(question, sources)

        return {
            "tool": "web_search",
            "question": question,
            "search_query": search_query,
            "answer": answer or "No relevant web results were found.",
            "sources": sources,
            "grounded": bool(sources),
        }

    @staticmethod
    def _synthesize_answer(question: str, sources: List[Dict[str, Any]]) -> str:
        if not sources:
            return ""

        context_snippets = "\n\n".join(
            f"Source [{i+1}] ({source.get('title', '')} - {source.get('url', '')}):\n{source.get('content', '')}"
            for i, source in enumerate(sources[:5])
            if source.get("content")
        )
        if not context_snippets:
            return WebSearchTool._fallback_answer(sources)

        try:
            from backend.services.llm import ask_llm
            prompt = f"""You are a helpful enterprise AI assistant.
Answer the user's question accurately and concisely based on the following web search results.
Synthesize the key facts directly into a clear answer.

Web Search Results:
{context_snippets}

User Question:
{question}

Answer:"""
            llm_answer = ask_llm(prompt, temperature=0.2)
            if llm_answer and llm_answer.strip():
                return llm_answer.strip()
        except Exception as e:
            logger.debug("LLM synthesis error for web search: %s", e)

        return WebSearchTool._fallback_answer(sources)

    @staticmethod
    def _normalise_query(question: str, conversation_history: str = "") -> str:
        """Remove local-document framing, extract context from history, and constrain known queries."""
        cleaned = " ".join(str(question or "").split()).strip()

        directive_pattern = (
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:search|find|look\s*up|check|browse)"
            r"(?:\s+(?:it|this|that|for\s+it))?(?:\s+(?:from|on|via|in|using))?"
            r"(?:\s+(?:the\s+)?(?:web|internet|online|google))?[\s.?!]*$"
        )
        is_pure_directive = bool(re.match(directive_pattern, cleaned, re.IGNORECASE)) or cleaned.lower() in {
            "search from web", "search on web", "from web", "from the web",
            "web search", "search online", "look it up", "search it", "google it",
            "search the web", "look up on web", "find on web"
        }

        if is_pure_directive and conversation_history:
            user_questions = re.findall(r"(?:User|Human):\s*(.+)", conversation_history, re.IGNORECASE)
            if user_questions:
                for prev in reversed(user_questions):
                    prev_clean = prev.strip()
                    if prev_clean and not bool(re.match(directive_pattern, prev_clean, re.IGNORECASE)):
                        cleaned = prev_clean
                        break

        # Remove filler prefixes like "search from web for ...", "search online for ..."
        cleaned = re.sub(
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:search(?:\s+(?:the\s+web|online|from\s+web|on\s+web|the\s+internet))?\s+(?:for\s+)?|look\s+up\s+(?:on\s+the\s+web\s+)?(?:for\s+)?)",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(
            r"(?:\s+(?:from|on|via)\s+(?:the\s+)?(?:web|internet|online))[\s.?!]*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        query = cleaned or " ".join(str(question or "").split())
        if WebSearchTool._is_python_release_question(query):
            return "latest official stable Python release site:python.org"
        return query

    @staticmethod
    def _is_python_release_question(question: str) -> bool:
        normalized = str(question or "").lower()
        return (
            "python" in normalized
            and ("latest" in normalized or "most recent" in normalized)
            and ("stable" in normalized or "release" in normalized or "version" in normalized)
        )

    @staticmethod
    def _official_python_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        official = [
            source
            for source in sources
            if "python.org" in str(source.get("url", "")).lower()
            and "discuss.python.org" not in str(source.get("url", "")).lower()
        ]
        return official or sources

    @staticmethod
    def _python_release_answer(sources: List[Dict[str, Any]]) -> str:
        versions = set()
        for source in WebSearchTool._official_python_sources(sources):
            haystack = " ".join(
                str(source.get(field, ""))
                for field in ("title", "url", "content")
            )
            for match in re.findall(r"(?:Python[\s\u202f]*)?(\d+\.\d+\.\d+)", haystack, flags=re.IGNORECASE):
                versions.add(tuple(int(part) for part in match.split(".")))
        if not versions:
            return ""
        latest = ".".join(str(part) for part in max(versions))
        return f"The official Python sources list Python {latest} as the latest stable release."

    @staticmethod
    def _normalise_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        for result in results:
            url = str(result.get("url", "")).strip()
            if not url:
                continue
            sources.append(
                {
                    "title": str(result.get("title", "Untitled source")).strip(),
                    "url": url,
                    "content": str(result.get("content", "")).strip(),
                    "score": result.get("score"),
                }
            )
        return sources

    @staticmethod
    def _fallback_answer(sources: List[Dict[str, Any]]) -> str:
        snippets = [
            f"{source['title']}: {source['content']}"
            for source in sources
            if source.get("content")
        ]
        return "\n\n".join(snippets[:5])

    @staticmethod
    def _error(answer: str, error: str) -> Dict[str, Any]:
        return {
            "tool": "web_search",
            "answer": answer,
            "sources": [],
            "error": error,
            "grounded": False,
        }


web_search_tool = WebSearchTool()
