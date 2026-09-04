import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger("enterprise_agent")

class AgentStatus(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskState:
    task_id: str
    description: str
    status: str
    tool: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retry_count: int = 0

@dataclass
class AgentState:
    session_id: str
    user_id: int
    original_question: str
    status: AgentStatus
    current_step: str
    execution_plan: Optional[Dict[str, Any]] = None
    tasks: List[TaskState] = field(default_factory=list)
    current_task_index: int = 0
    intermediate_results: List[Dict[str, Any]] = field(default_factory=list)
    final_answer: Optional[str] = None
    reflection_results: Optional[Dict[str, Any]] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

class AgenticStateManager:
    def __init__(self):
        self.active_sessions: Dict[str, AgentState] = {}
        self.max_session_history = 100
    
    def create_session(self, session_id: str, user_id: int, question: str) -> AgentState:
        """
        Create a new agent session for handling a complex question.
        """
        state = AgentState(
            session_id=session_id,
            user_id=user_id,
            original_question=question,
            status=AgentStatus.PLANNING,
            current_step="initialization"
        )
        
        self.active_sessions[session_id] = state
        logger.info(f"Created new agent session: {session_id}")
        
        return state
    
    def get_session(self, session_id: str) -> Optional[AgentState]:
        """
        Retrieve an existing agent session.
        """
        return self.active_sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: AgentStatus, current_step: str = "") -> None:
        """
        Update the status of an agent session.
        """
        state = self.get_session(session_id)
        if state:
            state.status = status
            if current_step:
                state.current_step = current_step
            state.updated_at = datetime.now().isoformat()
            logger.info(f"Session {session_id} status updated to {status}")
    
    def add_task(self, session_id: str, task_id: str, description: str, tool: str, input_data: Dict[str, Any]) -> None:
        """
        Add a task to the agent session.
        """
        state = self.get_session(session_id)
        if state:
            task = TaskState(
                task_id=task_id,
                description=description,
                status="pending",
                tool=tool,
                input_data=input_data,
                start_time=datetime.now().isoformat()
            )
            state.tasks.append(task)
            state.updated_at = datetime.now().isoformat()
    
    def update_task_status(self, session_id: str, task_id: str, status: str, output_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        """
        Update the status of a specific task.
        """
        state = self.get_session(session_id)
        if state:
            for task in state.tasks:
                if task.task_id == task_id:
                    task.status = status
                    if output_data:
                        task.output_data = output_data
                    if error_message:
                        task.error_message = error_message
                    if status in ["completed", "failed"]:
                        task.end_time = datetime.now().isoformat()
                    break
            state.updated_at = datetime.now().isoformat()
    
    def add_intermediate_result(self, session_id: str, result: Dict[str, Any]) -> None:
        """
        Add an intermediate result to the session.
        """
        state = self.get_session(session_id)
        if state:
            state.intermediate_results.append(result)
            state.updated_at = datetime.now().isoformat()
    
    def set_final_answer(self, session_id: str, answer: str) -> None:
        """
        Set the final answer for the session.
        """
        state = self.get_session(session_id)
        if state:
            state.final_answer = answer
            state.status = AgentStatus.COMPLETED
            state.current_step = "completed"
            state.updated_at = datetime.now().isoformat()
            logger.info(f"Session {session_id} completed with final answer")
    
    def add_reflection_result(self, session_id: str, reflection: Dict[str, Any]) -> None:
        """
        Add reflection analysis results to the session.
        """
        state = self.get_session(session_id)
        if state:
            state.reflection_results = reflection
            state.updated_at = datetime.now().isoformat()
    
    def add_error(self, session_id: str, error: Exception, context: Dict[str, Any]) -> None:
        """
        Add an error to the session's error history.
        """
        state = self.get_session(session_id)
        if state:
            error_record = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            state.error_history.append(error_record)
            state.updated_at = datetime.now().isoformat()
            logger.error(f"Error in session {session_id}: {error}")
    
    def set_execution_plan(self, session_id: str, plan: Dict[str, Any]) -> None:
        """
        Set the execution plan for the session.
        """
        state = self.get_session(session_id)
        if state:
            state.execution_plan = plan
            state.updated_at = datetime.now().isoformat()
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the session for debugging/monitoring.
        """
        state = self.get_session(session_id)
        if not state:
            return None
        
        return {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "original_question": state.original_question,
            "status": state.status.value,
            "current_step": state.current_step,
            "total_tasks": len(state.tasks),
            "completed_tasks": len([t for t in state.tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in state.tasks if t.status == "failed"]),
            "intermediate_results_count": len(state.intermediate_results),
            "has_final_answer": state.final_answer is not None,
            "total_errors": len(state.error_history),
            "created_at": state.created_at,
            "updated_at": state.updated_at
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old sessions to prevent memory leaks.
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, state in self.active_sessions.items():
            try:
                created_time = datetime.fromisoformat(state.created_at)
                if created_time < cutoff_time:
                    sessions_to_remove.append(session_id)
            except:
                # If we can't parse the time, remove it to be safe
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
        
        return len(sessions_to_remove)
    
    def export_session_state(self, session_id: str) -> Optional[str]:
        """
        Export session state as JSON for debugging or persistence.
        """
        state = self.get_session(session_id)
        if not state:
            return None
        
        # Convert to serializable format
        state_dict = {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "original_question": state.original_question,
            "status": state.status.value,
            "current_step": state.current_step,
            "execution_plan": state.execution_plan,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "status": task.status,
                    "tool": task.tool,
                    "input_data": task.input_data,
                    "output_data": task.output_data,
                    "error_message": task.error_message,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    "retry_count": task.retry_count
                }
                for task in state.tasks
            ],
            "intermediate_results": state.intermediate_results,
            "final_answer": state.final_answer,
            "reflection_results": state.reflection_results,
            "error_history": state.error_history,
            "metadata": state.metadata,
            "created_at": state.created_at,
            "updated_at": state.updated_at
        }
        
        return json.dumps(state_dict, indent=2)
    
    def get_conversation_context(self, session_id: str) -> str:
        """
        Get formatted conversation context for use in prompts.
        """
        state = self.get_session(session_id)
        if not state:
            return ""
        
        context_parts = [f"Original Question: {state.original_question}"]
        
        if state.intermediate_results:
            context_parts.append("\nPrevious Steps:")
            for i, result in enumerate(state.intermediate_results, 1):
                context_parts.append(f"Step {i}: {result.get('answer', 'No answer')}")
        
        if state.error_history:
            context_parts.append(f"\nPrevious Errors: {len(state.error_history)}")
        
        return "\n".join(context_parts)

agentic_state_manager = AgenticStateManager()