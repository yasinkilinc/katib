"""
Session Memory - Short-term memory for current session.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ToolCallRecord:
    """Record of a tool call"""
    tool_name: str
    arguments: Dict[str, Any]
    success: bool
    timestamp: str
    execution_time_ms: float
    error: Optional[str] = None
    is_important: bool = False

@dataclass  
class SessionMemory:
    """
    Short-term memory for the current session.
    Tracks tool calls, intents, and context.
    """
    session_id: str
    started_at: str
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    intents: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def record_intent(self, intent: str):
        """Record a user intent"""
        self.intents.append(intent)
    
    def record_tool_call(self, tool_name: str, arguments: Dict[str, Any], 
                         success: bool, execution_time_ms: float, error: str = None, 
                         is_important: bool = False):
        """Record a tool call"""
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            success=success,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time_ms,
            error=error,
            is_important=is_important
        )
        self.tool_calls.append(record)
    
    def get_recent_failures(self, limit: int = 5) -> List[ToolCallRecord]:
        """Get recent failed tool calls"""
        failures = [tc for tc in self.tool_calls if not tc.success]
        return failures[-limit:]
    
    def get_context_summary(self) -> str:
        """Get a summary for LLM context"""
        recent_tools = [tc.tool_name for tc in self.tool_calls[-5:]]
        recent_intents = self.intents[-3:]
        
        return f"Recent tools: {', '.join(recent_tools)}. Recent intents: {'; '.join(recent_intents)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "success": tc.success,
                    "timestamp": tc.timestamp
                }
                for tc in self.tool_calls
            ],
            "intents": self.intents,
            "context": self.context
        }


class MemoryManager:
    """
    Manages both session (short-term) and persistent (long-term) memory.
    """
    
    def __init__(self, memory_file: str = "data/memory.json"):
        self.memory_file = memory_file
        self.current_session: Optional[SessionMemory] = None
        self._start_session()
    
    def _start_session(self):
        """Start a new session"""
        import uuid
        self.current_session = SessionMemory(
            session_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat()
        )
    
    def record_intent(self, intent: str):
        """Record user intent"""
        if self.current_session:
            self.current_session.record_intent(intent)
    
    def record_tool_call(self, tool_name: str, arguments: Dict[str, Any],
                         success: bool, execution_time_ms: float, error: str = None,
                         is_important: bool = False):
        """Record a tool call"""
        if self.current_session:
            self.current_session.record_tool_call(
                tool_name, arguments, success, execution_time_ms, error, is_important
            )
    
    def get_session_context(self) -> str:
        """Get context summary for LLM"""
        if self.current_session:
            return self.current_session.get_context_summary()
        return ""
    
    def save_session(self):
        """Save session to persistent storage"""
        import os
        
        if not self.current_session:
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        # Load existing data
        try:
            with open(self.memory_file, "r") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "sessions" not in data:
                    data = {"sessions": []}
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"sessions": []}
        
        # Add current session
        data["sessions"].append(self.current_session.to_dict())
        
        # Keep only last 100 sessions
        data["sessions"] = data["sessions"][-100:]
        
        # Save
        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_similar_past_failures(self, tool_name: str, limit: int = 3) -> List[Dict]:
        """Get past failures for a specific tool"""
        try:
            with open(self.memory_file, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        failures = []
        for session in data.get("sessions", []):
            for tc in session.get("tool_calls", []):
                if tc.get("tool_name") == tool_name and not tc.get("success"):
                    failures.append(tc)
        
        return failures[-limit:]


# Singleton
_memory: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory
