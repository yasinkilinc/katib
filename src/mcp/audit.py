"""
Audit Logger - Automatic logging for all capability calls
"""
import json
import os
import time
from typing import Optional, Dict, Any
from dataclasses import asdict
from .capabilities import CapabilityRequest, ExecutionResult, CapabilityStatus

class AuditLogger:
    """
    Logs all capability requests and their outcomes.
    This is a natural byproduct of MCP - not an afterthought.
    """
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "audit.jsonl")
        os.makedirs(log_dir, exist_ok=True)
    
    def log_request(self, request: CapabilityRequest, status: CapabilityStatus, 
                    policy_reason: Optional[str] = None):
        """Log a capability request with its policy decision"""
        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "request",
            "capability": request.name,
            "parameters": request.parameters,
            "origin": request.origin.value,
            "context_id": request.context_id,
            "status": status.value,
            "policy_reason": policy_reason
        }
        self._write(entry)
    
    def log_execution(self, request: CapabilityRequest, result: ExecutionResult):
        """Log the result of capability execution"""
        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "execution",
            "capability": request.name,
            "context_id": request.context_id,
            "success": result.success,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms
        }
        self._write(entry)
    
    def log_rollback(self, original_capability: str, rollback_capability: str, 
                     context_id: str, success: bool):
        """Log a rollback action"""
        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "rollback",
            "original_capability": original_capability,
            "rollback_capability": rollback_capability,
            "context_id": context_id,
            "success": success
        }
        self._write(entry)
    
    def _write(self, entry: Dict[str, Any]):
        """Append entry to JSONL file"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[!] Audit log write failed: {e}")
    
    def get_recent_failures(self, capability: str, limit: int = 10) -> list:
        """Get recent failures for a specific capability (for policy decisions)"""
        failures = []
        try:
            if not os.path.exists(self.log_file):
                return []
            
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if (entry.get("type") == "execution" and 
                        entry.get("capability") == capability and
                        not entry.get("success")):
                        failures.append(entry)
            
            return failures[-limit:]  # Return most recent
        except Exception as e:
            print(f"[!] Audit log read failed: {e}")
            return []

# Global singleton
_audit_logger: Optional[AuditLogger] = None

def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
