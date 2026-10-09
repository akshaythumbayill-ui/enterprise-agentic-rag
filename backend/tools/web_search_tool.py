import os
import re
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class WebSearchTool:
    """Search the public web through Tavily and return grounded source records."""

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def run(self, question: str, max_results: int | None = None) -> Dict[str, Any]:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
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

        configured_results = os.getenv("TAVILY_MAX_RESULTS", "5")
        try:
            result_count = max_results or int(configured_results)
        except ValueError:
            result_count = 5
        result_count = min(max(result_count, 1), 10)

        search_query = self._normalise_query(question)
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
        except requests.Timeout:
            return self._error("Web search timed out. Please try again.", "timeout")
        except requests.RequestException as error:
            return self._error("Web search is temporarily unavailable.", str(error))
        except ValueError:
            return self._error("Web search returned an invalid response.", "invalid_json")

        sources = self._normalise_sources(data.get("results", []))
        answer = (data.get("answer") or "").strip()
        if self._is_python_release_question(question):
            authoritative_answer = self._python_release_answer(sources)
            if authoritative_answer:
                answer = authoritative_answer
                sources = self._official_python_sources(sources)
        if not answer:
            answer = self._fallback_answer(sources)

        return {
            "tool": "web_search",
            "question": question,
            "search_query": search_query,
            "answer": answer or "No relevant web results were found.",
            "sources": sources,
            "grounded": bool(sources),
        }

    @staticmethod
    def _normalise_query(question: str) -> str:
        """Remove local-document framing and constrain known authoritative queries."""
        query = " ".join(str(question or "").split())
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
