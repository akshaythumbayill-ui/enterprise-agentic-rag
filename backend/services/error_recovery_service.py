import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger("enterprise_agent")

class RecoveryStrategy(Enum):
    RETRY_SAME = "retry_same"
    RETRY_ALTERNATIVE = "retry_alternative"
    FALLBACK_DEFAULT = "fallback_default"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ABORT = "abort"

@dataclass
class ErrorContext:
    error: Exception
    tool: str
    operation: str
    retry_count: int
    context_data: Dict[str, Any]
    timestamp: float

@dataclass
class RecoveryAction:
    strategy: RecoveryStrategy
    action_description: str
    modified_params: Optional[Dict[str, Any]] = None
    alternative_tool: Optional[str] = None

class ErrorRecoveryService:
    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        self.error_patterns = {
            "decommissioned": RecoveryStrategy.RETRY_ALTERNATIVE,
            "not_found": RecoveryStrategy.RETRY_ALTERNATIVE,
            "timeout": RecoveryStrategy.RETRY_SAME,
            "rate_limit": RecoveryStrategy.RETRY_SAME,
            "authentication": RecoveryStrategy.ABORT,
            "permission": RecoveryStrategy.ABORT,
            "validation": RecoveryStrategy.RETRY_ALTERNATIVE,
            "network": RecoveryStrategy.RETRY_SAME,
        }
    
    def analyze_error(self, error: Exception, tool: str, operation: str, context: Dict[str, Any]) -> ErrorContext:
        """
        Analyze an error and create an error context for recovery decision making.
        """
        return ErrorContext(
            error=error,
            tool=tool,
            operation=operation,
            retry_count=context.get("retry_count", 0),
            context_data=context,
            timestamp=time.time()
        )
    
    def determine_recovery_strategy(self, error_context: ErrorContext) -> RecoveryAction:
        """
        Determine the best recovery strategy based on error analysis.
        """
        error_message = str(error_context.error).lower()
        error_type = type(error_context.error).__name__
        
        # Check for specific error patterns
        for pattern, strategy in self.error_patterns.items():
            if pattern in error_message or pattern in error_type.lower():
                return self._create_recovery_action(strategy, error_context)
        
        # Default strategy based on retry count
        if error_context.retry_count >= self.max_retries:
            return RecoveryAction(
                strategy=RecoveryStrategy.ABORT,
                action_description="Max retries reached, aborting operation"
            )
        
        # Try same operation first for unknown errors
        return RecoveryAction(
            strategy=RecoveryStrategy.RETRY_SAME,
            action_description="Retrying same operation"
        )
    
    def _create_recovery_action(self, strategy: RecoveryStrategy, error_context: ErrorContext) -> RecoveryAction:
        """
        Create a specific recovery action based on strategy.
        """
        if strategy == RecoveryStrategy.RETRY_ALTERNATIVE:
            alternative_tool = self._suggest_alternative_tool(error_context.tool)
            return RecoveryAction(
                strategy=strategy,
                action_description=f"Retrying with alternative tool: {alternative_tool}",
                alternative_tool=alternative_tool
            )
        
        elif strategy == RecoveryStrategy.FALLBACK_DEFAULT:
            return RecoveryAction(
                strategy=strategy,
                action_description="Using fallback default response"
            )
        
        elif strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
            return RecoveryAction(
                strategy=strategy,
                action_description="Skipping failed step and continuing with chain"
            )
        
        elif strategy == RecoveryStrategy.ABORT:
            return RecoveryAction(
                strategy=strategy,
                action_description="Aborting operation due to unrecoverable error"
            )
        
        else:  # RETRY_SAME
            return RecoveryAction(
                strategy=strategy,
                action_description="Retrying same operation with exponential backoff"
            )
    
    def _suggest_alternative_tool(self, failed_tool: str) -> Optional[str]:
        """
        Suggest an alternative tool based on the failed tool.
        """
        tool_alternatives = {
            "rag": None,  # No good alternative for RAG
            "calculator": None,  # No good alternative for calculator
            "time": None,  # No good alternative for time
        }
        
        return tool_alternatives.get(failed_tool)
    
    def execute_recovery(self, 
                        operation: Callable, 
                        recovery_action: RecoveryAction, 
                        error_context: ErrorContext) -> Any:
        """
        Execute the recovery action.
        """
        if recovery_action.strategy == RecoveryStrategy.RETRY_SAME:
            return self._retry_with_backoff(operation, error_context)
        
        elif recovery_action.strategy == RecoveryStrategy.RETRY_ALTERNATIVE:
            if recovery_action.alternative_tool:
                return self._retry_with_alternative(operation, recovery_action.alternative_tool, error_context)
            else:
                return self._retry_with_backoff(operation, error_context)
        
        elif recovery_action.strategy == RecoveryStrategy.FALLBACK_DEFAULT:
            return self._provide_fallback_response(error_context)
        
        elif recovery_action.strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
            return self._skip_operation(error_context)
        
        elif recovery_action.strategy == RecoveryStrategy.ABORT:
            raise error_context.error
        
        else:
            raise ValueError(f"Unknown recovery strategy: {recovery_action.strategy}")
    
    def _retry_with_backoff(self, operation: Callable, error_context: ErrorContext) -> Any:
        """
        Retry operation with exponential backoff.
        """
        retry_index = min(error_context.retry_count, len(self.retry_delays) - 1)
        delay = self.retry_delays[retry_index]
        
        logger.info(f"Retrying operation after {delay}s (attempt {error_context.retry_count + 1})")
        time.sleep(delay)
        
        return operation()
    
    def _retry_with_alternative(self, operation: Callable, alternative_tool: str, error_context: ErrorContext) -> Any:
        """
        Retry operation with alternative tool (placeholder for implementation).
        """
        logger.info(f"Attempting to use alternative tool: {alternative_tool}")
        # This would need to be implemented based on specific tool switching logic
        return operation()
    
    def _provide_fallback_response(self, error_context: ErrorContext) -> Dict[str, Any]:
        """
        Provide a fallback response when recovery is not possible.
        """
        return {
            "answer": f"I encountered an error: {str(error_context.error)}. Please try again or rephrase your question.",
            "error": str(error_context.error),
            "status": "fallback"
        }
    
    def _skip_operation(self, error_context: ErrorContext) -> Dict[str, Any]:
        """
        Skip the failed operation and return a continuation signal.
        """
        return {
            "answer": "Skipping this step due to error.",
            "error": str(error_context.error),
            "status": "skipped"
        }
    
    def should_retry(self, error_context: ErrorContext) -> bool:
        """
        Determine if an operation should be retried based on error context.
        """
        # Don't retry authentication/permission errors
        error_message = str(error_context.error).lower()
        if any(term in error_message for term in ["authentication", "permission", "unauthorized"]):
            return False
        
        # Don't retry if max retries reached
        if error_context.retry_count >= self.max_retries:
            return False
        
        # Retry for network-related errors
        if any(term in error_message for term in ["timeout", "network", "connection"]):
            return True
        
        # Retry for rate limiting
        if "rate limit" in error_message:
            return True
        
        # Default: retry once
        return error_context.retry_count == 0

error_recovery_service = ErrorRecoveryService()