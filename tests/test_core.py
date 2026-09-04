from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from tools.calculator_tool import run as calculate
from tools.time_tool import run as current_time
from services import database_service
from services import rag_service
from services.auth_service import hash_password, verify_password
from services.planner_service import greeting_response, select_tool


def test_calculator_handles_basic_math():
    assert calculate("What is 12 times 3?")["answer"] == "36"


def test_calculator_rejects_division_by_zero():
    assert "Division by zero" in calculate("1 / 0")["answer"]


def test_time_tool_returns_answer():
    assert current_time()["answer"]


def test_greetings_get_a_direct_response():
    assert greeting_response("Hello!") == "Hello! How can I help you today?"
    assert select_tool("good morning") == "greeting"
    assert greeting_response("hello there") is None


def test_agentic_greeting_works():
    from services.agentic_graph_service import simple_execution_node

    result = simple_execution_node({
        "question": "hi",
        "user_id": 1,
        "session_id": "greeting-test",
        "conversation_history": "",
    })

    assert result["chain_result"]["answer"] == "Hi! How can I help you today?"


def test_user_conversations_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(database_service, "DATABASE_PATH", Path(tmp_path) / "test.db")
    database_service.init_database()
    first = database_service.create_user("first_user", "hash")
    second = database_service.create_user("second_user", "hash")
    database_service.save_turn(first["id"], "session-a", "question", "answer")

    assert len(database_service.get_messages(first["id"], "session-a")) == 2
    with pytest.raises(PermissionError):
        database_service.get_messages(second["id"], "session-a")


def test_rag_falls_back_without_an_index(monkeypatch):
    def missing_index(question, user_id, k=2):
        raise FileNotFoundError

    monkeypatch.setattr(rag_service, "retrieve_documents", missing_index)
    result = rag_service.answer_question("policy?", 1)

    assert result["sources"] == []
    assert "No indexed documents" in result["answer"]


def test_password_hashing_supports_long_passphrases():
    password = "a" * 100
    password_hash = hash_password(password)
    assert verify_password(password, password_hash) is True


def test_oversized_login_password_is_invalid():
    password_hash = hash_password("valid-password")
    assert verify_password("a" * 100, password_hash) is False
