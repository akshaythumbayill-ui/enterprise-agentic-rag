import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "backend" / "tools" / "web_search_tool.py"
spec = importlib.util.spec_from_file_location("web_search_tool_under_test", MODULE_PATH)
web_search_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(web_search_module)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_tavily_results_are_normalised(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    session = FakeSession(
        FakeResponse(
            {
                "answer": "The answer from Tavily.",
                "results": [
                    {
                        "title": "Example source",
                        "url": "https://example.com/source",
                        "content": "Supporting content.",
                        "score": 0.91,
                    }
                ],
            }
        )
    )

    result = web_search_module.WebSearchTool(session).run("latest product news")

    assert result["tool"] == "web_search"
    assert result["answer"] == "The answer from Tavily."
    assert result["grounded"] is True
    assert result["sources"][0]["url"] == "https://example.com/source"
    assert session.calls[0][1]["json"]["query"] == "latest product news"


def test_missing_tavily_key_is_actionable(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    result = web_search_module.WebSearchTool().run("search online")

    assert result["grounded"] is False
    assert "TAVILY_API_KEY" in result["answer"]
    assert result["sources"] == []


def test_python_release_queries_use_official_sources_and_exact_version(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    session = FakeSession(
        FakeResponse(
            {
                "answer": "Python 3.13.10 is the latest stable release.",
                "results": [
                    {
                        "title": "Python 3.14.7 documentation",
                        "url": "https://docs.python.org/3/whatsnew/3.14.html",
                        "content": "Python 3.14.7 documentation and release details.",
                    },
                    {
                        "title": "Unrelated blog",
                        "url": "https://example.com/python",
                        "content": "Python 3.15.0 is rumored.",
                    },
                ],
            }
        )
    )

    result = web_search_module.WebSearchTool(session).run(
        "Use my uploaded handbook and current web sources. What is the latest official stable Python release?"
    )

    assert result["answer"] == "The official Python sources list Python 3.14.7 as the latest stable release."
    assert result["search_query"] == "latest official stable Python release site:python.org"
    assert result["sources"] == [
        {
            "title": "Python 3.14.7 documentation",
            "url": "https://docs.python.org/3/whatsnew/3.14.html",
            "content": "Python 3.14.7 documentation and release details.",
            "score": None,
        }
    ]
