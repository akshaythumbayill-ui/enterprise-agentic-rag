from typing import Dict, Any
import uuid

from .agentic_graph_service import agentic_graph
from .agentic_state_service import agentic_state_manager

def route_question_agentic(
    question: str,
    conversation_history: str,
    user_id: int,
) -> Dict[str, Any]:
    """
    Route questions through the agentic RAG system with multi-step reasoning,
    reflection, and adaptive capabilities.
    """
    # Generate session ID for this interaction
    session_id = str(uuid.uuid4())
    
    # Prepare initial state for the agentic graph
    initial_state = {
        "question": question,
        "user_id": user_id,
        "session_id": session_id,
        "conversation_history": conversation_history,
        "execution_plan": None,
        "tool_chain": None,
        "chain_result": None,
        "reflection_result": None,
        "final_answer": None,
        "should_retry": False,
        "retry_count": 0,
        "status": "initial"
    }
    
    try:
        # Execute the agentic workflow
        final_state = agentic_graph.invoke(initial_state)
        
        # Extract final results
        final_answer = final_state.get("final_answer", "")
        selected_tool = final_state.get("selected_tool", "agentic")
        sources = final_state.get("sources", [])
        
        # Get session summary for debugging
        session_summary = agentic_state_manager.get_session_summary(session_id)
        
        return {
            "question": question,
            "answer": final_answer,
            "selected_tool": selected_tool,
            "sources": sources,
            "session_id": session_id,
            "agentic": True,
            "session_summary": session_summary
        }
        
    except Exception as e:
        # Log the error and provide fallback response
        agentic_state_manager.add_error(session_id, e, {"operation": "agentic_execution"})
        
        return {
            "question": question,
            "answer": f"I encountered an error during agentic processing: {str(e)}. Please try again.",
            "selected_tool": "error",
            "sources": [],
            "session_id": session_id,
            "agentic": True,
            "error": str(e)
        }

def get_session_debug_info(session_id: str) -> Dict[str, Any]:
    """
    Get detailed debug information about an agentic session.
    """
    session_state = agentic_state_manager.get_session(session_id)
    if not session_state:
        return {"error": "Session not found"}
    
    return {
        "summary": agentic_state_manager.get_session_summary(session_id),
        "full_state": agentic_state_manager.export_session_state(session_id)
    }