from typing import Dict, Callable, Any
from .capabilities import CapabilityRequest, ExecutionResult

class Registry:
    def __init__(self):
        self._executors: Dict[str, Any] = {}
        # Mapping: "web.search" -> (executor_instance, method_name)
        self._capability_map: Dict[str, tuple] = {}

    def register_executor(self, name: str, executor_instance: Any):
        """
        Registers an executor and discovers its public methods as capabilities.
        Executor methods must be public and not start with_.
        """
        self._executors[name] = executor_instance
        
        # Auto-discovery of capabilities
        # Convention: methods of executor are capabilities
        # But for now, we rely on the executor to handle the dispatch in 'execute'
        # Or we map specific actions.
        # Simple v1: Map executor_name to instance. The resolver logic handles the rest.
        pass

    def get_executor(self, capability_name: str) -> Any:
        """
        Routing logic:
        web.* -> windsurf_executor (if browsing) or specific web executor
        app.* -> macos_executor
        system.* -> macos_executor
        file.* -> macos_executor
        interpreter.* -> interpreter_executor
        """
        prefix = capability_name.split('.')[0]
        
        if capability_name == "system.stop":
            return self._executors.get("system_executor")
            
        if prefix in ["app", "system", "file", "keyboard", "mouse", "tts", "screen"]:
            return self._executors.get("macos_executor")
        elif prefix in ["interpreter", "math", "text"]:
            return self._executors.get("interpreter_executor")
        elif prefix in ["web"]:
            # Prefer windsurf if available for web actions, or a dedicated web tool
            # For now, map to macos_executor which might handle 'open_url'
            # OR map to windsurf if advanced.
            # Let's map to macos_executor for basic web.navigate
            return self._executors.get("macos_executor")
        elif prefix in ["terminal"]:
            return self._executors.get("terminal_executor")
            
        return None
