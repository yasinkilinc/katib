import json
import os
import time
import re
from typing import Dict, Any, Union

from src.utils.secure_storage import SecureStorage

class MemoryEngine:
    def __init__(self, storage_path="memory.json", encryption_key=None):
        self.storage_path = storage_path
        self.history = []
        self.secure_storage = SecureStorage(encryption_key)
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    encrypted_data = f.read()
                # Decrypt the data
                decrypted_data = self.secure_storage.decrypt_data(encrypted_data)
                self.history = decrypted_data
            except Exception:
                # If decryption fails, initialize with empty history
                self.history = []

    def _save(self):
        # Sanitize data before saving
        sanitized_history = self.sanitize_data(self.history)
        # Encrypt the data before saving
        encrypted_data = self.secure_storage.encrypt_data(sanitized_history)
        with open(self.storage_path, 'w') as f:
            f.write(encrypted_data)

    def _sanitize_value(self, value: str) -> str:
        """
        Sanitize a single string value by detecting and masking sensitive data.
        """
        if not isinstance(value, str):
            return value

        # Define patterns for sensitive data
        patterns = [
            # Password fields
            (r'password["\']?\s*[:=]\s*["\']?([^"\']{6,}?)["\']?', r'\1', '***PASSWORD***'),
            # API keys (common formats)
            (r'(api[_-]?key|secret)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', r'\2', '***API_KEY***'),
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', None, '[EMAIL_REDACTED]'),
            # Credit card numbers (basic pattern)
            (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', None, '***CREDIT_CARD***'),
            # Phone numbers (basic pattern)
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', None, '***PHONE***'),
            # IP addresses
            (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', None, '***IP_ADDRESS***'),
            # SSN pattern (XXX-XX-XXXX)
            (r'\b\d{3}-\d{2}-\d{4}\b', None, '***SSN***'),
            # Bank account numbers (simple pattern for 8-17 digits)
            (r'\b\d{8,17}\b', None, '***ACCOUNT_NUMBER***'),
            # VIN numbers (17-character alphanumeric)
            (r'\b[A-HJ-NPR-Z0-9]{17}\b', None, '***VIN***'),
            # Bitcoin wallet addresses
            (r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', None, '***BITCOIN_ADDRESS***'),
            # Ethereum addresses
            (r'\b0x[a-fA-F0-9]{40}\b', None, '***ETHEREUM_ADDRESS***'),
        ]

        sanitized_value = value
        for pattern, capture_group_pattern, replacement in patterns:
            if capture_group_pattern:
                # Handle cases where we want to capture and replace a specific group
                matches = re.findall(pattern, sanitized_value, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # If multiple groups captured, use the first one that's not empty
                        for m in match:
                            if m and m != replacement:
                                sanitized_value = re.sub(re.escape(m), replacement, sanitized_value)
                    else:
                        # If single group captured
                        if match and match != replacement:
                            sanitized_value = re.sub(re.escape(match), replacement, sanitized_value)
            else:
                # Direct substitution
                sanitized_value = re.sub(pattern, replacement, sanitized_value, flags=re.IGNORECASE)

        return sanitized_value

    def sanitize_data(self, data: Union[Dict, list, str]) -> Union[Dict, list, str]:
        """
        Recursively sanitize data structures by detecting and masking sensitive information.
        """
        if isinstance(data, dict):
            sanitized_dict = {}
            for key, value in data.items():
                # Check if key indicates sensitive data regardless of value
                lower_key = str(key).lower()
                if any(sensitive_word in lower_key for sensitive_word in ['password', 'token', 'secret', 'key', 'credential', 'auth', 'passphrase', 'cert', 'license']):
                    sanitized_dict[key] = '***REDACTED***'
                else:
                    sanitized_dict[key] = self.sanitize_data(value)
            return sanitized_dict
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_value(data)
        else:
            return data

    def detect_sensitive_data(self, data: Union[Dict, list, str]) -> list:
        """
        Detect and return a list of sensitive data types found in the input data.
        """
        detections = []

        if isinstance(data, dict):
            for key, value in data.items():
                lower_key = str(key).lower()
                if any(sensitive_word in lower_key for sensitive_word in ['password', 'token', 'secret', 'key', 'credential', 'auth', 'passphrase', 'cert', 'license']):
                    detections.append({
                        'type': 'SENSITIVE_KEY',
                        'key': key,
                        'location': 'dict_key'
                    })

                detections.extend(self.detect_sensitive_data(value))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                detections.extend(self.detect_sensitive_data(item))
        elif isinstance(data, str):
            # Define patterns for sensitive data detection
            patterns = [
                (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
                (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 'CREDIT_CARD'),
                (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'PHONE'),
                (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'IP_ADDRESS'),
                (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
                (r'\b\d{8,17}\b', 'ACCOUNT_NUMBER'),
                (r'\b[A-HJ-NPR-Z0-9]{17}\b', 'VIN'),
                (r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', 'BITCOIN_ADDRESS'),
                (r'\b0x[a-fA-F0-9]{40}\b', 'ETHEREUM_ADDRESS'),
                (r'(api[_-]?key|secret)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', 'API_KEY'),
                (r'password["\']?\s*[:=]\s*["\']?([^"\']{6,}?)["\']?', 'PASSWORD')
            ]

            for pattern, data_type in patterns:
                matches = re.findall(pattern, data, re.IGNORECASE)
                for match in matches:
                    # Handle capture groups appropriately
                    if isinstance(match, tuple):
                        detected_value = match[0] if match else ''
                    else:
                        detected_value = match
                    if detected_value and len(str(detected_value)) > 0:
                        detections.append({
                            'type': data_type,
                            'value': str(detected_value),
                            'location': 'string_content'
                        })

        return detections

    def record_execution(self, outcome: Dict[str, Any]):
        """
        Records the full cycle: Command -> Plan -> Execution Result
        """
        # Detect sensitive data in the outcome before sanitizing
        detections = self.detect_sensitive_data(outcome)

        # Sanitize the outcome before recording
        sanitized_outcome = self.sanitize_data(outcome)

        entry = {
            "timestamp": time.time(),
            "command": sanitized_outcome.get("command"),
            "intent": sanitized_outcome.get("intent"),
            "plan": sanitized_outcome.get("plan"),
            "results": sanitized_outcome.get("actions"), # List of capability request/result
            "success": sanitized_outcome.get("success"),
            "error": sanitized_outcome.get("error"),
            "sensitive_data_detected": len(detections) > 0,
            "detection_summary": detections[:10]  # Limit to first 10 detections for performance
        }

        self.history.append(entry)
        # Keep last 1000
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self._save()

        # Log to audit trail if sensitive data was detected
        if detections:
            self.audit_log(outcome, source="record_execution")

    def get_recent_context(self, limit=5):
        return self.history[-limit:]

    def audit_log(self, data: Union[Dict, list, str], source: str = "unknown"):
        """
        Creates an audit log entry for sensitive data detection and sanitization.
        """
        detections = self.detect_sensitive_data(data)
        if detections:
            audit_entry = {
                "timestamp": time.time(),
                "source": source,
                "sensitive_data_found": len(detections),
                "detection_details": detections,
                "sanitized_data": self.sanitize_data(data)
            }

            # Save audit log separately from main memory with encryption
            audit_path = "audit_log.json"
            audit_history = []
            if os.path.exists(audit_path):
                try:
                    with open(audit_path, 'r') as f:
                        encrypted_audit_data = f.read()
                    # Decrypt the audit data
                    decrypted_audit_data = self.secure_storage.decrypt_data(encrypted_audit_data)
                    audit_history = decrypted_audit_data
                except:
                    audit_history = []

            audit_history.append(audit_entry)
            # Keep last 500 audit entries
            if len(audit_history) > 500:
                audit_history = audit_history[-500:]

            # Encrypt the audit history before saving
            encrypted_audit_history = self.secure_storage.encrypt_data(audit_history)
            with open(audit_path, 'w') as f:
                f.write(encrypted_audit_history)

        return detections
