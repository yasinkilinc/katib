from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from ..mcp.capabilities import ExecutionResult

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the specific action.
        Must return ExecutionResult, never raise.
        """
        pass

    def validate(self, action: str, params: Dict[str, Any]) -> bool:
        """Optional pre-check."""
        return True
