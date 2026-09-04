from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class ChainStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class ChainStep:
    step_id: str
    tool: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: ChainStatus = ChainStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class ToolChain:
    chain_id: str
    steps: List[ChainStep]
    current_step_index: int = 0
    status: ChainStatus = ChainStatus.PENDING
    final_result: Optional[Dict[str, Any]] = None

class ToolChainingService:
    def __init__(self):
        self.max_retries = 2
        self.timeout_seconds = 30
    
    def create_chain(self, question: str, plan: Any) -> ToolChain:
        """
        Create a tool chain from an execution plan.
        """
        from .agentic_planner_service import ExecutionPlan
        
        if not isinstance(plan, ExecutionPlan) or not plan.tasks:
            # Fallback to simple single-step chain
            return self._create_simple_chain(question)
        
        steps = []
        for task in plan.tasks:
            step = ChainStep(
                step_id=task.id,
                tool=task.tool,
                input_data=task.input_data,
                dependencies=task.dependencies,
                status=ChainStatus.PENDING
            )
            steps.append(step)
        
        return ToolChain(
            chain_id=f"chain_{id(question)}",
            steps=steps,
            current_step_index=0,
            status=ChainStatus.PENDING
        )
    
    def _create_simple_chain(self, question: str) -> ToolChain:
        """
        Create a simple single-step chain for non-complex questions.
        """
        from .planner_service import select_tool
        
        tool = select_tool(question)
        step = ChainStep(
            step_id="simple_step",
            tool=tool,
            input_data={"question": question},
            status=ChainStatus.PENDING
        )
        
        return ToolChain(
            chain_id=f"simple_chain_{id(question)}",
            steps=[step],
            current_step_index=0,
            status=ChainStatus.PENDING
        )
    
    def execute_chain(self, chain: ToolChain, user_id: int, conversation_history: str = "") -> Dict[str, Any]:
        """
        Execute a tool chain with dependency resolution and error handling.
        """
        chain.status = ChainStatus.IN_PROGRESS
        
        # Execute steps in dependency order
        executed_steps = 0
        max_iterations = len(chain.steps) * 2  # Prevent infinite loops
        
        while executed_steps < len(chain.steps) and max_iterations > 0:
            max_iterations -= 1
            
            # Find next executable step
            next_step = self._find_next_executable_step(chain)
            
            if not next_step:
                # No more steps can be executed
                break
            
            # Check if dependencies are satisfied
            if not self._check_dependencies(chain, next_step):
                # Skip if dependencies not met
                next_step.status = ChainStatus.SKIPPED
                continue
            
            # Execute the step
            try:
                result = self._execute_step(next_step, user_id, conversation_history, chain)
                next_step.output_data = result
                next_step.status = ChainStatus.COMPLETED
                executed_steps += 1
                
            except Exception as e:
                next_step.error_message = str(e)
                next_step.status = ChainStatus.FAILED
                
                # Retry logic
                if next_step.retry_count < self.max_retries:
                    next_step.retry_count += 1
                    next_step.status = ChainStatus.PENDING
                    continue
                else:
                    # Max retries reached, mark as failed
                    pass
        
        # Determine final chain status
        if all(step.status in [ChainStatus.COMPLETED, ChainStatus.SKIPPED] for step in chain.steps):
            chain.status = ChainStatus.COMPLETED
        elif any(step.status == ChainStatus.FAILED for step in chain.steps):
            chain.status = ChainStatus.FAILED
        else:
            chain.status = ChainStatus.IN_PROGRESS
        
        # Collect final result
        chain.final_result = self._collect_chain_result(chain)
        
        return chain.final_result
    
    def _find_next_executable_step(self, chain: ToolChain) -> Optional[ChainStep]:
        """
        Find the next step that can be executed based on dependencies and status.
        """
        for step in chain.steps:
            if step.status == ChainStatus.PENDING:
                return step
        return None
    
    def _check_dependencies(self, chain: ToolChain, step: ChainStep) -> bool:
        """
        Check if all dependencies for a step are satisfied.
        """
        if not step.dependencies:
            return True
        
        for dep_id in step.dependencies:
            dep_step = next((s for s in chain.steps if s.step_id == dep_id), None)
            if not dep_step or dep_step.status != ChainStatus.COMPLETED:
                return False
        
        return True
    
    def _execute_step(self, step: ChainStep, user_id: int, conversation_history: str, chain: ToolChain) -> Dict[str, Any]:
        """
        Execute a single step in the chain.
        """
        from tools import calculator_tool, rag_tool, time_tool
        
        # Prepare input data, potentially using outputs from previous steps
        input_data = self._prepare_step_input(step, chain)
        
        if step.tool == "rag":
            question = input_data.get("question", "")
            return rag_tool.run(question, user_id, conversation_history)
        
        elif step.tool == "calculator":
            question = input_data.get("question", "")
            return calculator_tool.run(question)
        
        elif step.tool == "time":
            return time_tool.run()
        
        else:
            raise ValueError(f"Unknown tool: {step.tool}")
    
    def _prepare_step_input(self, step: ChainStep, chain: ToolChain) -> Dict[str, Any]:
        """
        Prepare input data for a step, potentially using outputs from dependency steps.
        """
        input_data = step.input_data.copy()
        
        # If input_data is empty, use the original question from the chain context
        if not input_data:
            # Try to get question from the first step
            if chain.steps:
                input_data["question"] = chain.steps[0].input_data.get("question", "")
        
        # Inject outputs from dependency steps if needed
        for dep_id in step.dependencies:
            dep_step = next((s for s in chain.steps if s.step_id == dep_id), None)
            if dep_step and dep_step.output_data:
                input_data[f"dep_{dep_id}_output"] = dep_step.output_data
        
        return input_data
    
    def _collect_chain_result(self, chain: ToolChain) -> Dict[str, Any]:
        """
        Collect the final result from the chain execution.
        """
        completed_steps = [step for step in chain.steps if step.status == ChainStatus.COMPLETED]
        
        if not completed_steps:
            return {
                "answer": "All steps in the chain failed to execute.",
                "status": "failed",
                "steps_executed": 0
            }
        
        if len(completed_steps) == 1:
            return completed_steps[0].output_data or {
                "answer": "Step completed but produced no output.",
                "status": "completed"
            }
        
        # Multiple steps - return all results for synthesis
        return {
            "answer": "Multi-step execution completed. Results ready for synthesis.",
            "status": "completed",
            "steps_executed": len(completed_steps),
            "step_results": [step.output_data for step in completed_steps],
            "chain_id": chain.chain_id
        }

tool_chaining_service = ToolChainingService()