from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .planner_service import greeting_response, select_tool
from backend.tools import (
    calculator_tool,
    rag_tool,
    time_tool,
    web_search_tool,
)


class AgentState(TypedDict, total=False):
    question: str
    user_id: int
    conversation_history: str
    selected_tool: str
    result: dict[str, Any]

def planner_node(state: AgentState):
    return {
        "selected_tool": select_tool(
            state["question"],
            state.get("conversation_history", ""),
        )
    }


def greeting_node(state: AgentState):
    return {
        "result": {
            "question": state["question"],
            "answer": greeting_response(state["question"]),
            "sources": [],
        }
    }


def rag_node(state: AgentState):
    return {
        "result": rag_tool.run(
            state["question"],
            state["user_id"],
            state.get("conversation_history", ""),
        )
    }


def time_node(state: AgentState):
    return {
        "result": time_tool.run()
    }


def calculator_node(state: AgentState):
    return {
        "result": calculator_tool.run(state["question"])
    }


def web_search_node(state: AgentState):
    return {
        "result": web_search_tool.run(state["question"])
    }


def select_tool_path(state: AgentState):
    return state["selected_tool"]


workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("greeting", greeting_node)
workflow.add_node("rag", rag_node)
workflow.add_node("time", time_node)
workflow.add_node("calculator", calculator_node)
workflow.add_node("web_search", web_search_node)

workflow.add_edge(START, "planner")

workflow.add_conditional_edges(
    "planner",
    select_tool_path,
    {
        "greeting": "greeting",
        "rag": "rag",
        "time": "time",
        "calculator": "calculator",
        "web_search": "web_search",
    },
)

workflow.add_edge("rag", END)
workflow.add_edge("time", END)
workflow.add_edge("calculator", END)
workflow.add_edge("web_search", END)
workflow.add_edge("greeting", END)

agent_graph = workflow.compile()
