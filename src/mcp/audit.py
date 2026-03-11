"""
Audit Logger - Automatic logging for all capability calls
"""
import json
import os
import time
import re
from typing import Optional, Dict, Any, Union
from enum import Enum
from .capabilities import CapabilityRequest, ExecutionResult

class CapabilityStatus(Enum):
    ALLOWED = "allowed"
    DENIED_POLICY = "denied_policy"
    DENIED_AUTH = "denied_auth"
    DENIED_OTHER = "denied_other"

class AuditLogger:
    """
    Logs all capability requests and their outcomes.
    This is a natural byproduct of MCP - not an afterthought.
    """

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "audit.jsonl")
        os.makedirs(log_dir, exist_ok=True)

        # Sensitive data patterns to detect
        self.sensitive_patterns = [
            # Password fields
            r"(?i)(password|passwd|pwd)",
            # API keys and tokens
            r"(?i)(api[_-]?key|token|secret|credential|auth)",
            # Credit card numbers
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            # Email addresses (could contain sensitive info)
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            # SSN pattern
            r"\b\d{3}-?\d{2}-?\d{4}\b",
            # Phone numbers
            r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
        ]

        # Precompile regex patterns for performance
        self.compiled_patterns = [re.compile(pattern) for pattern in self.sensitive_patterns]

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize individual values by detecting and redacting sensitive information"""
        if isinstance(value, str):
            # Check if the value itself looks like sensitive data
            lower_val = value.lower()
            if ('password' in lower_val or 'token' in lower_val or 'secret' in lower_val or
                'key' in lower_val or len(value) > 20 and value.replace('-', '').isdigit()):
                # Redact long alphanumeric strings that might be sensitive
                return "***REDACTED***"

            # Apply regex patterns to detect and redact sensitive patterns in the string
            sanitized = value
            for pattern in self.compiled_patterns:
                if pattern.search(sanitized):
                    sanitized = pattern.sub("***REDACTED***", sanitized)
            return sanitized

        elif isinstance(value, dict):
            return self._sanitize_dict(value)

        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]

        else:
            return value

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary by detecting and redacting sensitive fields"""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Check if the key indicates sensitive data
            if isinstance(key, str):
                is_sensitive_key = False
                # Manually check each compiled pattern for sensitive key detection
                for pattern in self.compiled_patterns[:2]:  # Only check password/api patterns for keys
                    if pattern.search(key):  # Fixed: call search on the compiled pattern
                        is_sensitive_key = True
                        break

                if is_sensitive_key:
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_value(value)
            else:
                sanitized[key] = self._sanitize_value(value)

        return sanitized
    
    def log_request(self, request: CapabilityRequest, status: CapabilityStatus,
                    policy_reason: Optional[str] = None):
        """Log a capability request with its policy decision"""
        # Sanitize the parameters before logging
        sanitized_parameters = self._sanitize_dict(request.parameters) if request.parameters else {}

        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "request",
            "capability": request.name,
            "parameters": sanitized_parameters,
            "origin": request.origin.value,
            "context_id": request.context_id,
            "status": status.value,
            "policy_reason": policy_reason
        }
        self._write(entry)
    
    def log_execution(self, request: CapabilityRequest, result: ExecutionResult):
        """Log the result of capability execution"""
        # Sanitize the parameters before logging
        sanitized_parameters = self._sanitize_dict(request.parameters) if request.parameters else {}

        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "execution",
            "capability": request.name,
            "context_id": request.context_id,
            "parameters": sanitized_parameters,
            "success": result.success,
            "error": self._sanitize_value(result.error) if result.error else None,
            "execution_time_ms": result.execution_time_ms
        }
        self._write(entry)
    
    def log_rollback(self, original_capability: str, rollback_capability: str,
                     context_id: str, success: bool, parameters: Optional[Dict] = None):
        """Log a rollback action"""
        # Sanitize the parameters before logging if provided
        sanitized_parameters = self._sanitize_dict(parameters) if parameters else {}

        entry = {
            "ts": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "rollback",
            "original_capability": original_capability,
            "rollback_capability": rollback_capability,
            "context_id": context_id,
            "parameters": sanitized_parameters,
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
