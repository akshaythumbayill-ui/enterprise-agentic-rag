from typing import Any, TypedDict, Optional
from enum import Enum

from langgraph.graph import END, START, StateGraph

from .agentic_planner_service import agentic_planner, ExecutionPlan
from .tool_chaining_service import tool_chaining_service, ToolChain
from .reflection_service import reflection_service, ReflectionResult
from .error_recovery_service import error_recovery_service, ErrorContext
from .agentic_state_service import agentic_state_manager, AgentStatus
try:
    from backend.tools import calculator_tool, rag_tool, time_tool, web_search_tool
except ModuleNotFoundError:
    from tools import calculator_tool, rag_tool, time_tool, web_search_tool

class AgenticAgentState(TypedDict, total=False):
    question: str
    user_id: int
    session_id: str
    conversation_history: str
    execution_plan: Optional[ExecutionPlan]
    tool_chain: Optional[ToolChain]
    chain_result: Optional[dict[str, Any]]
    reflection_result: Optional[ReflectionResult]
    final_answer: Optional[str]
    sources: list[dict[str, Any]]
    should_retry: bool
    retry_count: int
    status: str

class RouteDecision(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    REFLECT = "reflect"
    RETRY = "retry"
    SYNTHESIZE = "synthesize"
    COMPLETE = "complete"
    FAILED = "failed"

def _filter_sources_for_question(question: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep source links aligned with authoritative-source requirements."""
    normalized = str(question or "").lower()
    if (
        "python" in normalized
        and "latest" in normalized
        and ("stable" in normalized or "release" in normalized or "version" in normalized)
    ):
        return [
            source
            for source in sources
            if "discuss.python.org" not in str((source or {}).get("url", "")).lower()
        ]
    return sources

def planning_node(state: AgenticAgentState):
    """Plan the execution approach - simple vs complex, task decomposition."""
    session_id = state.get("session_id", str(hash(state["question"])))
    user_id = state["user_id"]
    question = state["question"]
    conversation_history = state.get("conversation_history", "")
    
    # Create or get session
    agent_state = agentic_state_manager.get_session(session_id)
    if not agent_state:
        agent_state = agentic_state_manager.create_session(session_id, user_id, question)
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.PLANNING, "task_decomposition")
    
    # Determine complexity and create execution plan
    execution_plan = agentic_planner.decompose_question(question, conversation_history)
    
    # Store plan in session
    agentic_state_manager.set_execution_plan(session_id, {
        "is_complex": len(execution_plan.tasks) > 0,
        "tasks_count": len(execution_plan.tasks),
        "requires_synthesis": execution_plan.requires_synthesis
    })
    
    return {
        "execution_plan": execution_plan,
        "status": "planning_complete"
    }

def route_planning_decision(state: AgenticAgentState):
    """Decide whether to use simple or complex execution path."""
    execution_plan = state.get("execution_plan")
    
    if not execution_plan or not execution_plan.tasks:
        return RouteDecision.SIMPLE.value
    else:
        return RouteDecision.COMPLEX.value

def simple_execution_node(state: AgenticAgentState):
    """Execute simple single-tool queries."""
    from .planner_service import greeting_response, select_tool
    
    question = state["question"]
    user_id = state["user_id"]
    conversation_history = state.get("conversation_history", "")
    session_id = state.get("session_id", str(hash(question)))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.EXECUTING, "simple_execution")
    
    # Select tool
    tool = select_tool(question, conversation_history)
    
    # Add task to session
    agentic_state_manager.add_task(
        session_id, 
        "simple_task", 
        f"Execute {tool} tool", 
        tool, 
        {"question": question}
    )
    
    # Execute tool
    try:
        if tool == "greeting":
            greeting = greeting_response(question) or "Hi! How can I help you today?"
            result = {
                "answer": greeting,
                "tool": "greeting",
                "sources": []
            }
        elif tool == "rag":
            result = rag_tool.run(question, user_id, conversation_history)
        elif tool == "calculator":
            result = calculator_tool.run(question)
        elif tool == "time":
            result = time_tool.run()
        elif tool == "web_search":
            result = web_search_tool.run(
                question,
                conversation_history=conversation_history,
            )
        else:
            result = {"answer": "Unknown tool selected", "tool": tool, "sources": []}
        
        agentic_state_manager.update_task_status(session_id, "simple_task", "completed", result)
        agentic_state_manager.add_intermediate_result(session_id, result)
        
        return {
            "chain_result": result,
            "should_retry": False,
            "status": "simple_complete"
        }
        
    except Exception as e:
        agentic_state_manager.update_task_status(session_id, "simple_task", "failed", error_message=str(e))
        agentic_state_manager.add_error(session_id, e, {"tool": tool, "question": question})
        
        return {
            "chain_result": {"answer": f"Error: {str(e)}", "error": str(e)},
            "should_retry": True,
            "status": "simple_failed"
        }

def complex_execution_node(state: AgenticAgentState):
    """Execute complex multi-step workflows using tool chaining."""
    execution_plan = state.get("execution_plan")
    question = state["question"]
    user_id = state["user_id"]
    conversation_history = state.get("conversation_history", "")
    session_id = state.get("session_id", str(hash(question)))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.EXECUTING, "complex_execution")
    
    # Create tool chain from execution plan
    tool_chain = tool_chaining_service.create_chain(question, execution_plan)
    
    # Add tasks to session
    for step in tool_chain.steps:
        agentic_state_manager.add_task(
            session_id,
            step.step_id,
            step.tool,
            step.tool,
            step.input_data
        )
    
    # Execute chain
    try:
        chain_result = tool_chaining_service.execute_chain(tool_chain, user_id, conversation_history)
        
        # Update task statuses in session
        for step in tool_chain.steps:
            status = "completed" if step.status.value == "completed" else "failed"
            agentic_state_manager.update_task_status(
                session_id,
                step.step_id,
                status,
                step.output_data,
                step.error_message
            )
        
        agentic_state_manager.add_intermediate_result(session_id, chain_result)
        
        return {
            "tool_chain": tool_chain,
            "chain_result": chain_result,
            "should_retry": chain_result.get("status") == "failed",
            "status": "complex_complete"
        }
        
    except Exception as e:
        agentic_state_manager.add_error(session_id, e, {"execution": "complex_chain"})
        
        return {
            "chain_result": {"answer": f"Chain execution failed: {str(e)}", "error": str(e)},
            "should_retry": True,
            "status": "complex_failed"
        }

def reflection_node(state: AgenticAgentState):
    """Reflect on answer quality and determine if improvement is needed."""
    question = state["question"]
    chain_result = state.get("chain_result", {})
    session_id = state.get("session_id", str(hash(question)))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.REFLECTING, "quality_evaluation")
    
    # Get answer and context
    answer = chain_result.get("answer", "")
    tool_used = chain_result.get("tool", "unknown")
    context = agentic_state_manager.get_conversation_context(session_id)
    
    # Evaluate answer quality
    reflection_result = reflection_service.evaluate_answer(
        question, answer, context, tool_used
    )
    
    # Store reflection results
    agentic_state_manager.add_reflection_result(session_id, {
        "quality_score": reflection_result.answer_quality,
        "needs_improvement": reflection_result.needs_improvement,
        "confidence": reflection_result.confidence,
        "should_retry": reflection_result.should_retry
    })
    
    return {
        "reflection_result": reflection_result,
        "should_retry": reflection_result.should_retry,
        "status": "reflection_complete"
    }

def route_reflection_decision(state: AgenticAgentState):
    """Decide whether to retry, synthesize, or complete based on reflection."""
    reflection_result = state.get("reflection_result")
    execution_plan = state.get("execution_plan")
    
    if not reflection_result:
        return RouteDecision.COMPLETE.value
    
    # If reflection suggests retry and we haven't retried too many times
    retry_count = state.get("retry_count", 0)
    if reflection_result.should_retry and retry_count < 2:
        return RouteDecision.RETRY.value
    
    # If complex execution with synthesis required
    if execution_plan and execution_plan.requires_synthesis:
        return RouteDecision.SYNTHESIZE.value
    
    # Otherwise complete
    return RouteDecision.COMPLETE.value

def synthesis_node(state: AgenticAgentState):
    """Synthesize results from multiple tasks into a coherent answer."""
    question = state["question"]
    chain_result = state.get("chain_result", {})
    session_id = state.get("session_id", str(hash(question)))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.SYNTHESIZING, "result_synthesis")
    
    # Get task results
    task_results = chain_result.get("step_results", [])
    if not task_results:
        # Fallback to single result
        task_results = [chain_result] if chain_result else []
    
    # Synthesize results and preserve citations from every contributing task.
    sources = []
    for result in task_results:
        for source in (result or {}).get("sources", []):
            if source not in sources:
                sources.append(source)
    for source in chain_result.get("sources", []):
        if source not in sources:
            sources.append(source)

    try:
        final_answer = reflection_service.synthesize_multi_task_results(question, task_results)
        sources = _filter_sources_for_question(question, sources)
        
        agentic_state_manager.set_final_answer(session_id, final_answer)
        
        return {
            "final_answer": final_answer,
            "sources": sources,
            "status": "synthesis_complete"
        }
        
    except Exception as e:
        agentic_state_manager.add_error(session_id, e, {"operation": "synthesis"})
        
        # Fallback: use first result
        fallback_answer = task_results[0].get("answer", "Synthesis failed") if task_results else "No results available"
        
        return {
            "final_answer": fallback_answer,
            "sources": sources,
            "status": "synthesis_fallback"
        }

def retry_node(state: AgenticAgentState):
    """Handle retry logic with modified parameters."""
    retry_count = state.get("retry_count", 0)
    session_id = state.get("session_id", str(hash(state["question"])))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.EXECUTING, f"retry_attempt_{retry_count + 1}")
    
    # Simple retry logic - increment retry count and re-route
    return {
        "retry_count": retry_count + 1,
        "should_retry": False,  # Will be set by execution node
        "status": "retry_initiated"
    }

def completion_node(state: AgenticAgentState):
    """Finalize the answer and prepare response."""
    chain_result = state.get("chain_result", {})
    final_answer = state.get("final_answer")
    session_id = state.get("session_id", str(hash(state["question"])))
    
    agentic_state_manager.update_session_status(session_id, AgentStatus.COMPLETED, "finalizing")
    
    # Determine final answer
    if final_answer:
        answer = final_answer
    elif chain_result:
        answer = chain_result.get("answer", "No answer generated")
    else:
        answer = "Failed to generate answer"
    
    # Ensure final answer is set in session
    agentic_state_manager.set_final_answer(session_id, answer)
    
    # Prepare final response
    selected_tool = chain_result.get("tool", "agentic_chain")
    sources = []
    for source in state.get("sources", []):
        if source not in sources:
            sources.append(source)
    for source in chain_result.get("sources", []):
        if source not in sources:
            sources.append(source)
    for result in chain_result.get("step_results", []):
        for source in (result or {}).get("sources", []):
            if source not in sources:
                sources.append(source)
    sources = _filter_sources_for_question(state.get("question", ""), sources)
    
    return {
        "final_answer": answer,
        "selected_tool": selected_tool,
        "sources": sources,
        "status": "completed"
    }

def route_completion_decision(state: AgenticAgentState):
    """Decide final routing after completion."""
    status = state.get("status", "")
    
    if "failed" in status.lower():
        return RouteDecision.FAILED.value
    else:
        return RouteDecision.COMPLETE.value

# Build the agentic workflow
def create_agentic_graph():
    workflow = StateGraph(AgenticAgentState)
    
    # Add nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("simple_execution", simple_execution_node)
    workflow.add_node("complex_execution", complex_execution_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("completion", completion_node)
    
    # Add edges
    workflow.add_edge(START, "planning")
    
    # Planning decision routing
    workflow.add_conditional_edges(
        "planning",
        route_planning_decision,
        {
            RouteDecision.SIMPLE.value: "simple_execution",
            RouteDecision.COMPLEX.value: "complex_execution"
        }
    )
    
    # Simple execution path
    workflow.add_edge("simple_execution", "reflection")
    
    # Complex execution path
    workflow.add_edge("complex_execution", "reflection")
    
    # Reflection decision routing
    workflow.add_conditional_edges(
        "reflection",
        route_reflection_decision,
        {
            RouteDecision.RETRY.value: "retry",
            RouteDecision.SYNTHESIZE.value: "synthesis",
            RouteDecision.COMPLETE.value: "completion"
        }
    )
    
    # Retry routing (back to execution based on original plan)
    workflow.add_conditional_edges(
        "retry",
        lambda state: "simple_execution" if not state.get("execution_plan") or not state["execution_plan"].tasks else "complex_execution",
        {
            "simple_execution": "simple_execution",
            "complex_execution": "complex_execution"
        }
    )
    
    # Synthesis to completion
    workflow.add_edge("synthesis", "completion")
    
    # Final completion
    workflow.add_edge("completion", END)
    
    return workflow.compile()

# Create the agentic graph
agentic_graph = create_agentic_graph()
