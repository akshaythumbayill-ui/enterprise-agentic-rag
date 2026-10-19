from backend.services.rag_service import answer_question


class RagTool:
    def run(
        self,
        question: str,
        user_id: int,
        conversation_history: str = "",
    ):
        return answer_question(
            question,
            user_id,
            conversation_history,
        )


rag_tool = RagTool()