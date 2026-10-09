from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.reflection_service import ReflectionService


def test_internal_task_markers_are_removed_without_damaging_text():
    answer = "Answer【Task 1 answer】. Next [Task 2 source]. Python【https://www.python.org/downloads/】."

    assert ReflectionService.clean_answer_markers(answer) == "Answer. Next. Python."

def test_synthesis_preserves_exact_mixed_source_facts():
    service = ReflectionService()
    result = service.synthesize_multi_task_results(
        "How many annual leave days and what is the latest official stable Python release?",
        [
            {
                "tool": "rag",
                "answer": "The handbook states 20 annual leave days.",
                "sources": [{
                    "filename": "employee_handbook.pdf",
                    "content": "Employees receive: 20 annual leave days.",
                }],
            },
            {
                "tool": "web_search",
                "answer": "The official Python sources list Python 3.14.7 as the latest stable release.",
                "sources": [{
                    "title": "Python 3.14.7 documentation",
                    "content": "Python 3.14.7 documentation and release details.",
                    "url": "https://docs.python.org/3/whatsnew/3.14.html",
                }],
            },
        ],
    )

    assert result == (
        "Employees receive 20 annual leave days according to the employee handbook. "
        "The latest official stable Python release is Python 3.14.7."
    )

