import sys
import io
import contextlib
import math
import json
import re
import datetime
import random
from typing import Dict, Any
from .base_executor import BaseExecutor, ExecutionResult

class InterpreterExecutor(BaseExecutor):
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        try:
            if action == "interpreter.run_python":
                code = params.get("code")
                return self._run_python(code)
            elif action == "interpreter.analyze":
                # Alias for run_python with safe intent
                code = params.get("code")
                return self._run_python(code)
            elif action == "interpreter.run_shell":
                return ExecutionResult(False, error="Shell execution is blocked by default policy until implemented securely.")
            else:
                return ExecutionResult(False, error=f"Unknown Interpreter action: {action}")
        except Exception as e:
            return ExecutionResult(False, error=str(e))

    def _run_python(self, code: str) -> ExecutionResult:
        if not code:
            return ExecutionResult(False, error="No code provided")

        # Capture stdout
        stdout_capture = io.StringIO()
        
        # Allowed builtins
        safe_globals = {
            "math": math,
            "json": json,
            "re": re,
            "datetime": datetime,
            "random": random,
            "print": print,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "len": len,
            "sorted": sorted,
            "max": max,
            "min": min,
            "sum": sum,
            "__builtins__": {} # Remove access to open, import, etc.
        }

        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(code, safe_globals)
            out = stdout_capture.getvalue()
            return ExecutionResult(True, data=out if out else "Done (No Output)")
        except Exception as e:
            return ExecutionResult(False, error=f"Python Error: {e}")
