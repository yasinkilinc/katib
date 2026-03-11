import ast
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

        # Validate the code using AST to check for unsafe operations
        try:
            parsed_ast = ast.parse(code)
            self._validate_ast(parsed_ast)
        except ValueError as e:
            return ExecutionResult(False, error=f"Security violation: {e}")
        except SyntaxError as e:
            return ExecutionResult(False, error=f"Syntax Error: {e}")

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

    def _validate_ast(self, node):
        """
        Recursively validate AST nodes to ensure they only contain safe operations.
        """
        for child in ast.walk(node):
            if isinstance(child, (
                ast.Import,
                ast.ImportFrom,
                ast.Call,
                ast.Attribute,
                ast.Name
            )):
                # Check for dangerous function calls
                if isinstance(child, ast.Call):
                    if self._is_dangerous_call(child):
                        raise ValueError(f"Potentially dangerous function call: {ast.dump(child)}")

                # Check for dangerous attribute access
                elif isinstance(child, ast.Attribute):
                    attr_name = child.attr
                    dangerous_attrs = [
                        '__import__', '__class__', '__mro__', '__bases__', '__subclasses__',
                        '__globals__', '__code__', '__closure__', '__func__',
                        'os', 'sys', 'subprocess', 'eval', 'exec', 'compile',
                        'open', 'file', 'input', 'raw_input'
                    ]
                    if attr_name in dangerous_attrs:
                        raise ValueError(f"Access to dangerous attribute: {attr_name}")

                # Check for dangerous imports
                elif isinstance(child, ast.Import):
                    for alias in child.names:
                        module_name = alias.name
                        if self._is_dangerous_module(module_name):
                            raise ValueError(f"Dangerous import: {module_name}")

                elif isinstance(child, ast.ImportFrom):
                    module_name = child.module
                    if self._is_dangerous_module(module_name):
                        raise ValueError(f"Dangerous import: {module_name}")

                    # Also check imported names
                    for alias in child.names:
                        name = alias.name
                        if name in ['eval', 'exec', 'compile', '__import__']:
                            raise ValueError(f"Dangerous import: {name} from {module_name}")

            # Check for other dangerous node types
            # Note: In Python 3.8+, Constant nodes represent what were formerly Str, Num, etc.
            elif isinstance(child, ast.Constant):
                # For now, we allow constants as they're just data
                pass

    def _is_dangerous_call(self, call_node):
        """
        Check if a function call is potentially dangerous.
        """
        func = call_node.func

        if isinstance(func, ast.Name):
            # Direct function call like eval(), exec(), etc.
            dangerous_functions = [
                'eval', 'exec', 'compile', 'open', 'file',
                'input', 'raw_input', '__import__'
            ]
            if func.id in dangerous_functions:
                return True

        elif isinstance(func, ast.Attribute):
            # Method call like os.system(), etc.
            attr_name = func.attr
            dangerous_methods = [
                'system', 'popen', 'remove', 'unlink', 'mkdir', 'rmdir',
                'chdir', 'chmod', 'kill', 'execv', 'execve', 'spawnv',
                'call', 'check_call', 'check_output'
            ]
            if attr_name in dangerous_methods:
                # Check if the object being called has dangerous attributes
                obj = func.value
                if isinstance(obj, ast.Name):
                    # This catches things like os.system, subprocess.call, etc.
                    if obj.id in ['os', 'subprocess', 'sys', 'importlib']:
                        return True
                elif isinstance(obj, ast.Attribute):
                    # Handle deeper nesting like os.path.join
                    pass

        return False

    def _is_dangerous_module(self, module_name):
        """
        Check if importing a module is potentially dangerous.
        """
        if module_name is None:
            return False

        dangerous_modules = [
            'os', 'subprocess', 'sys', 'importlib', 'imp',
            'pickle', 'marshal', 'shelve', 'ctypes',
            'socket', 'urllib.request', 'http.client',
            'ftplib', 'telnetlib', 'poplib', 'imaplib', 'smtplib',
            'xml.etree.ElementTree', 'xml.dom.minidom', 'xml.sax',
            'platform', 'pdb', 'webbrowser', 'cgi', 'cgitb',
            'runpy', 'code', 'codeop', 'py_compile', 'compileall',
            'zipfile', 'tarfile', 'tempfile', 'filecmp'
        ]

        # Check if the module is dangerous or starts with a dangerous module name
        for dangerous in dangerous_modules:
            if module_name == dangerous or module_name.startswith(dangerous + '.'):
                return True

        return False
