import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .llm import ask_llm

@dataclass
class ReflectionResult:
    answer_quality: float  # 0-1 scale
    needs_improvement: bool
    issues: list[str]
    suggested_improvements: list[str]
    confidence: float
    should_retry: bool

class ReflectionService:
    def __init__(self):
        self.quality_threshold = 0.6
        self.confidence_threshold = 0.5
    
    def evaluate_answer(self, question: str, answer: str, context: str = "", tool_used: str = "") -> ReflectionResult:
        """
        Evaluate the quality of an answer and determine if it needs improvement.
        """
        prompt = f"""
Evaluate the quality of the following answer to the given question.

Question: {question}
Answer: {answer}
Context: {context if context else "No additional context"}
Tool Used: {tool_used}

Evaluate based on:
1. Relevance: Does the answer directly address the question?
2. Accuracy: Is the information factually correct?
3. Completeness: Does it provide sufficient information?
4. Clarity: Is the answer clear and well-structured?
5. Confidence: How confident are you in this answer?

Return JSON format:
{{
    "quality_score": 0.0-1.0,
    "needs_improvement": true/false,
    "issues": ["list of specific issues"],
    "suggested_improvements": ["list of improvements"],
    "confidence": 0.0-1.0,
    "should_retry": true/false
}}
"""

        try:
            response = ask_llm(prompt, temperature=0.2)
            response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip(), flags=re.IGNORECASE)
            result = json.loads(response)
            
            return ReflectionResult(
                answer_quality=result.get("quality_score", 0.5),
                needs_improvement=result.get("needs_improvement", False),
                issues=result.get("issues", []),
                suggested_improvements=result.get("suggested_improvements", []),
                confidence=result.get("confidence", 0.5),
                should_retry=result.get("should_retry", False)
            )
            
        except Exception as e:
            # Fallback: basic quality assessment
            return self._basic_quality_assessment(question, answer, tool_used)
    
    def _basic_quality_assessment(self, question: str, answer: str, tool_used: str) -> ReflectionResult:
        """
        Fallback basic quality assessment when LLM evaluation fails.
        """
        issues = []
        quality_score = 0.7
        
        # Basic checks
        if not answer or len(answer.strip()) < 10:
            issues.append("Answer is too short or empty")
            quality_score = 0.2
        
        if "error" in answer.lower() or "failed" in answer.lower():
            issues.append("Answer contains error messages")
            quality_score = 0.3
        
        if "i don't know" in answer.lower() or "not available" in answer.lower():
            issues.append("Answer indicates information unavailability")
            quality_score = 0.4
        
        # Tool-specific checks
        if tool_used == "rag" and "could not find" in answer.lower():
            issues.append("RAG tool couldn't find relevant information")
            quality_score = 0.3
        
        if tool_used == "calculator" and "error" in answer.lower():
            issues.append("Calculator encountered an error")
            quality_score = 0.2
        
        needs_improvement = quality_score < self.quality_threshold
        should_retry = needs_improvement and quality_score < 0.4
        
        return ReflectionResult(
            answer_quality=quality_score,
            needs_improvement=needs_improvement,
            issues=issues,
            suggested_improvements=["Retry with different approach"] if should_retry else [],
            confidence=0.5,
            should_retry=should_retry
        )
    
    def synthesize_multi_task_results(self, question: str, task_results: list[Dict[str, Any]]) -> str:
        """
        Synthesize results from multiple tasks into a coherent answer.
        """
        if not task_results:
            return "No results available to synthesize."
        
        # If only one task, return its answer
        if len(task_results) == 1:
            return task_results[0].get("answer", "No answer available")
        
        # Multiple tasks - synthesize
        results_summary = "\n\n".join([
            f"Task {i+1} ({result.get('tool', 'unknown')}): {result.get('answer', 'No answer')}"
            for i, result in enumerate(task_results)
        ])
        
        prompt = f"""
Synthesize the following task results into a coherent answer to the original question.

Original Question: {question}

Task Results:
{results_summary}

Provide a well-structured answer that:
1. Directly addresses the original question
2. Incorporates relevant information from all tasks
3. Maintains logical flow and coherence
4. Acknowledges any conflicting information
"""

        try:
            return ask_llm(prompt, temperature=0.3)
        except Exception as e:
            # Fallback: concatenate results
            return f"Based on multiple tasks:\n" + results_summary

reflection_service = ReflectionService()