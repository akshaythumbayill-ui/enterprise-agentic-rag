from .graph_service import agent_graph



def route_question(
    question: str,
    conversation_history: str,
    user_id: int,
    agentic: bool = False,
):
    final_state = agent_graph.invoke(
        {
            "question": question,
            "conversation_history": conversation_history,
            "user_id": user_id,
            "agentic": agentic,
        }
    )

    return {
        "selected_tool": final_state["selected_tool"],
        **final_state["result"],
    }