import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass

from .llm import ask_llm

@dataclass
class Task:
    id: str
    description: str
    tool: str
    dependencies: List[str]
    input_data: Dict[str, Any]
    status: str = "pending"  # pending, in_progress, completed, failed

@dataclass
class ExecutionPlan:
    tasks: List[Task]
    final_answer_required: bool = True
    requires_synthesis: bool = False

class AgenticPlanner:
    def __init__(self):
        self.max_retries = 3
        self.confidence_threshold = 0.7
    
    def decompose_question(self, question: str, conversation_history: str = "") -> ExecutionPlan:
        """
        Decompose complex questions into sub-tasks for multi-step execution.
        """
        prompt = f"""
Analyze the following question and determine if it requires multi-step processing.

Question: {question}
Conversation history: {conversation_history}

Rules:
1. Simple questions (single tool) - return "simple"
2. Complex questions requiring multiple steps - decompose into sub-tasks
3. Questions requiring synthesis of multiple information sources - create synthesis tasks

Return JSON format:
{{
    "is_complex": true/false,
    "reasoning": "why this question is complex or simple",
    "tasks": [
        {{
            "id": "task_1",
            "description": "what this task should accomplish",
            "tool": "rag/calculator/time",
            "dependencies": [],
            "input_data": {{}}
        }}
    ],
    "requires_synthesis": true/false
}}

If simple, return: {{"is_complex": false, "reasoning": "...", "tasks": [], "requires_synthesis": false}}
"""

        try:
            response = ask_llm(prompt, temperature=0)
            response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip(), flags=re.IGNORECASE)
            result = json.loads(response)
            
            if not result.get("is_complex", False):
                return ExecutionPlan(tasks=[], final_answer_required=True, requires_synthesis=False)
            
            tasks = []
            for task_data in result.get("tasks", []):
                task = Task(
                    id=task_data["id"],
                    description=task_data["description"],
                    tool=task_data["tool"],
                    dependencies=task_data.get("dependencies", []),
                    input_data=task_data.get("input_data", {})
                )
                tasks.append(task)
            
            return ExecutionPlan(
                tasks=tasks,
                final_answer_required=True,
                requires_synthesis=result.get("requires_synthesis", False)
            )
            
        except Exception as e:
            # Fallback to simple processing
            return ExecutionPlan(tasks=[], final_answer_required=True, requires_synthesis=False)
    
    def create_fallback_tool_selection(self, question: str, conversation_history: str = "") -> str:
        """
        Fallback to simple tool selection for non-complex questions.
        """
        from .planner_service import select_tool
        return select_tool(question, conversation_history)
    
    def estimate_complexity(self, question: str) -> float:
        """
        Estimate complexity of a question (0-1 scale).
        """
        complexity_indicators = [
            "compare", "analyze", "evaluate", "synthesize", "combine",
            "multiple", "several", "both", "and", "then", "after",
            "calculate and", "find and", "what is and"
        ]
        
        question_lower = question.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in question_lower)
        
        # Simple heuristic: more indicators = higher complexity
        complexity = min(indicator_count * 0.2, 1.0)
        
        # Length also contributes to complexity
        if len(question.split()) > 15:
            complexity = min(complexity + 0.3, 1.0)
        
        return complexity

agentic_planner = AgenticPlanner()