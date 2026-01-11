from typing import Dict, Any, Optional
import time
from .registry import Registry
from .capabilities import CapabilityRequest, ExecutionResult, Origin
from ..core.policy import PolicyEngine, PolicyDecision

class Resolver:
    def __init__(self, registry: Registry, policy_engine: PolicyEngine):
        self.registry = registry
        self.policy = policy_engine

    def register_executor(self, name: str, executor: Any):
        self.registry.register_executor(name, executor)

    def resolve_and_execute(self, request: CapabilityRequest) -> ExecutionResult:
        start_time = time.time()
        
        # 1. Find Executor
        executor = self.registry.get_executor(request.name)
        if not executor:
            return ExecutionResult(
                success=False, 
                error=f"No executor found for capability: {request.name}"
            )

        # 2. Policy Check
        decision = self.policy.check_permission(request.name, request.parameters)
        
        if decision == PolicyDecision.DENY:
             return ExecutionResult(
                success=False, 
                error=f"Policy denied action: {request.name}"
            )
        
        if decision == PolicyDecision.REQUIRE_CONFIRMATION:
            # In a real async system, we would pause/callback. 
            # For this synchronous CLI loop, we ask via stdout (temporary).
            # In production GUI, this raises a UI Event.
            print(f"\n[!] Approval Required: Capability '{request.name}' requires user approval")
            print(f"    Capability: {request.name}")
            print(f"    Parameters: {request.parameters}")
            print(f"    Origin: {request.origin.value}")
            resp = input("    Approve? [y/N]: ")
            if resp.lower() != 'y':
                 return ExecutionResult(
                    success=False, 
                    error="User denied action."
                )

        # 3. Execute
        try:
            # Executors expect: execute(action, params)
            # action is the full capability string or the suffix?
            # Convention: pass full name 'web.search'
            if hasattr(executor, 'execute'):
                result = executor.execute(request.name, request.parameters)
            else:
                 return ExecutionResult(
                    success=False, 
                    error=f"Executor {executor} does not implement execute()"
                )
            
            # Ensure result is ExecutionResult
            if not isinstance(result, ExecutionResult):
                # Wrap legacy return (bool, msg)
                # This adapts old executors if any
                pass 
                
        except Exception as e:
             return ExecutionResult(
                success=False, 
                error=f"Execution exception: {str(e)}"
            )

        result.execution_time_ms = (time.time() - start_time) * 1000
        return result

# Singleton Instance (optional, for simple access)
_resolver_instance = None

def get_resolver() -> Resolver:
    global _resolver_instance
    if not _resolver_instance:
        # Lazy load due to cyclic deps if any
        reg = Registry()
        pol = PolicyEngine()
        _resolver_instance = Resolver(reg, pol)
    return _resolver_instance
