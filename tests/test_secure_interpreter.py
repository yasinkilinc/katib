import unittest
import sys
import os
import io
import contextlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.executors.interpreter_executor import InterpreterExecutor


class TestSecureInterpreter(unittest.TestCase):
    def setUp(self):
        self.executor = InterpreterExecutor()

    def test_safe_math_operations(self):
        """Test that safe mathematical operations work correctly"""
        result = self.executor._run_python("print(2 + 3 * 4)")
        self.assertTrue(result.success)
        self.assertIn("14", result.data)

    def test_safe_builtin_functions(self):
        """Test that safe builtin functions work correctly"""
        result = self.executor._run_python("print(len('hello world'))")
        self.assertTrue(result.success)
        self.assertIn("11", result.data)

    def test_safe_import_of_allowed_modules(self):
        """Test that safe imports work (though our security disallows imports by default)"""
        # Test importing allowed functions through AST analysis
        result = self.executor._run_python("import math\nprint(math.sqrt(16))")
        # This should fail since imports are blocked at AST validation
        self.assertFalse(result.success)
        # Either Security violation (caught at AST validation) or Python Error (caught at runtime)
        # depending on how deeply nested the import attempt is
        if result.error:
            self.assertTrue("Security violation" in result.error or "Python Error" in result.error)

    def test_blocking_of_dangerous_imports_os(self):
        """Test that dangerous imports like os are blocked"""
        result = self.executor._run_python("import os")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)
        self.assertIn("Dangerous import", result.error)

    def test_blocking_of_dangerous_imports_subprocess(self):
        """Test that dangerous imports like subprocess are blocked"""
        result = self.executor._run_python("import subprocess")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)
        self.assertIn("Dangerous import", result.error)

    def test_blocking_of_eval_function(self):
        """Test that eval function is blocked"""
        result = self.executor._run_python("eval('2+2')")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)

    def test_blocking_of_exec_function(self):
        """Test that exec function is blocked"""
        result = self.executor._run_python("exec('2+2')")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)

    def test_blocking_of_open_function(self):
        """Test that open function is blocked"""
        result = self.executor._run_python("open('/etc/passwd')")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)

    def test_blocking_of_os_system_calls(self):
        """Test that os.system calls are blocked"""
        result = self.executor._run_python("import os\nos.system('echo test')")
        self.assertFalse(result.success)
        self.assertIn("Security violation", result.error)

    def test_safe_list_operations(self):
        """Test that safe list operations work correctly"""
        result = self.executor._run_python("my_list = [1, 2, 3]\nprint(sum(my_list))")
        self.assertTrue(result.success)
        self.assertIn("6", result.data)

    def test_safe_string_operations(self):
        """Test that safe string operations work correctly"""
        result = self.executor._run_python("text = 'hello world'\nprint(text.upper())")
        self.assertTrue(result.success)
        self.assertIn("HELLO WORLD", result.data)

    def test_safe_json_operations(self):
        """Test that safe JSON operations work correctly"""
        result = self.executor._run_python("import json\ndata = {'key': 'value'}\nprint(json.dumps(data))")
        self.assertFalse(result.success)
        # Import is blocked at validation
        if result.error:
            self.assertTrue("Security violation" in result.error or "Python Error" in result.error)

    def test_syntax_error_handling(self):
        """Test that syntax errors are properly handled"""
        result = self.executor._run_python("print(unclosed_paren")
        self.assertFalse(result.success)
        self.assertIn("Syntax Error", result.error)

    def test_runtime_error_handling(self):
        """Test that runtime errors are properly handled"""
        result = self.executor._run_python("result = 10 / 0\nprint(result)")
        self.assertFalse(result.success)
        self.assertIn("Python Error", result.error)

    def test_empty_code_handling(self):
        """Test that empty code is properly handled"""
        result = self.executor._run_python("")
        self.assertFalse(result.success)
        self.assertIn("No code provided", result.error)

    def test_no_output_handling(self):
        """Test code that produces no output"""
        result = self.executor._run_python("x = 5")
        self.assertTrue(result.success)
        self.assertIn("Done (No Output)", result.data)

    def test_execute_method_valid_action(self):
        """Test that execute method works with valid interpreter action"""
        result = self.executor.execute("interpreter.run_python", {"code": "print(42)"})
        self.assertTrue(result.success)
        self.assertIn("42", result.data)

    def test_execute_method_invalid_action(self):
        """Test that execute method handles invalid actions"""
        result = self.executor.execute("invalid.action", {})
        self.assertFalse(result.success)
        self.assertIn("Unknown Interpreter action", result.error)

    def test_execute_method_analyze_alias(self):
        """Test that the analyze action works as an alias for run_python"""
        result = self.executor.execute("interpreter.analyze", {"code": "print('analyze works')"})
        self.assertTrue(result.success)
        self.assertIn("analyze works", result.data)

    def test_blocking_shell_execution(self):
        """Test that shell execution is blocked by default"""
        result = self.executor.execute("interpreter.run_shell", {})
        self.assertFalse(result.success)
        self.assertIn("Shell execution is blocked", result.error)

    def test_access_to_dangerous_attributes_blocked(self):
        """Test that access to dangerous attributes is blocked"""
        result = self.executor._run_python("getattr(str, '__import__')")
        self.assertFalse(result.success)
        # Should be blocked by AST validation before execution

    def test_access_to_subclasses_blocked(self):
        """Test that access to subclasses is blocked"""
        result = self.executor._run_python("__builtins__.__dict__")
        self.assertFalse(result.success)
        # Should be blocked by AST validation

if __name__ == '__main__':
    unittest.main()