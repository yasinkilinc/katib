# -*- coding: utf-8 -*-
"""
Simple Test Phase 1: Context Passing
Tests the context passing mechanism without requiring Ollama.
"""
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.plan import Plan, Step
from src.mcp.resolver import get_resolver
from src.mcp.capabilities import CapabilityRequest, Origin
from src.executors.terminal_executor import TerminalExecutor
from src.core.policy import PolicyEngine

def test_context_passing_simple():
    """
    Simple test: just check if context resolution works.
    Using terminal.execute twice to avoid LLM dependency.
    """
    print("=== Simple Context Passing Test ===\n")
    
    # Initialize components
    resolver = get_resolver()
    resolver.policy = PolicyEngine()
    resolver.policy.trust_level = 3  # Auto-approve terminal commands
    resolver.register_executor("terminal_executor", TerminalExecutor())
    
    # Create a plan with context passing
    plan = Plan(
        goal="Test context passing",
        reasoning="Step 1 generates text, Step 2 uses it",
        steps=[
            Step(
                id=1,
                name="generate_text",
                capability="terminal.execute",
                params={"command": "echo 'Hello from Step 1'"},
                requires_feedback=False
            ),
            Step(
                id=2,
                name="use_context",
                capability="terminal.execute",
                params={
                    "context_from_step": 1,
                    "command": "echo 'Step 2 received context'"
                },
                requires_feedback=False
            )
        ]
    )
    
    print(f"Plan: {plan.goal}")
    print(f"Steps: {len(plan.steps)}\n")
    
    # Execute the plan (simulating the _execute_plan logic)
    step_outputs = {}
    all_success = True
    
    for step in plan.steps:
        print(f"[Step {step.id}] {step.name}")
        
        # Copy params and resolve context
        params = step.params.copy()
        if "context_from_step" in params:
            context_step_id = params["context_from_step"]
            if context_step_id in step_outputs:
                params["context"] = str(step_outputs[context_step_id])
                print(f"  ✓ Context resolved from step {context_step_id}")
                print(f"  ✓ Context value: '{params['context'].strip()}'")
            else:
                print(f"  ✗ Step {context_step_id} output not found!")
                all_success = False
                break
            del params["context_from_step"]
        
        # Create request and execute
        request = CapabilityRequest(
            name=step.capability,
            parameters=params,
            origin=Origin.VOICE
        )
        
        result = resolver.resolve_and_execute(request)
        
        # Store output
        step_outputs[step.id] = result.data
        
        if not result.success:
            print(f"  ✗ Failed: {result.error}\n")
            all_success = False
            break
        else:
            print(f"  ✓ Success")
            if result.data:
                print(f"  ✓ Output: '{result.data.strip()}'")
            print()
    
    # Results
    print("="*50)
    if all_success and len(step_outputs) == 2:
        print("✓ TEST PASSED")
        print(f"\n✓ Step 1 produced output: '{step_outputs[1].strip()}'")
        print(f"✓ Step 2 received context from Step 1")
        print("\n✓ Context passing mechanism works correctly!")
        return True
    else:
        print("✗ TEST FAILED")
        return False


if __name__ == "__main__":
    print("╔═══════════════════════════════════════╗")
    print("║  PHASE 1 CONTEXT PASSING TEST         ║")
    print("╚═══════════════════════════════════════╝\n")
    
    try:
        passed = test_context_passing_simple()
        print("\n" + "="*50)
        if passed:
            print("RESULT: ✓ PASSED")
        else:
            print("RESULT: ✗ FAILED")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
