from collections import defaultdict, deque
from threading import Lock


class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.sessions = defaultdict(
            lambda: deque(maxlen=self.max_turns)
        )
        self.lock = Lock()

    def get_history(self, session_id: str) -> str:
        with self.lock:
            turns = list(self.sessions[session_id])

        if not turns:
            return "No previous conversation."

        return "\n".join(
            f"User: {turn['question']}\n"
            f"Assistant: {turn['answer']}"
            for turn in turns
        )

    def add_turn(
        self,
        session_id: str,
        question: str,
        answer: str,
    ):
        with self.lock:
            self.sessions[session_id].append(
                {
                    "question": question,
                    "answer": answer,
                }
            )

    def clear(self, session_id: str):
        with self.lock:
            self.sessions.pop(session_id, None)


memory = ConversationMemory()