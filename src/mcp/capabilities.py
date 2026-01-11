from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import time

class Origin(Enum):
    VOICE = "voice"
    TEXT = "text"
    AUTOMATION = "automation"
    SYSTEM = "system"

@dataclass
class CapabilityRequest:
    name: str                       # e.g. "web.search"
    parameters: Dict[str, Any]      # e.g. {"query": "foo"}
    origin: Origin = Origin.SYSTEM
    id: str = str(time.time())

@dataclass
class ExecutionResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
