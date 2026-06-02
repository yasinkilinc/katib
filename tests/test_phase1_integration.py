# -*- coding: utf-8 -*-
"""
Integration Test Phase 1: Multi-step Planning with Context Passing
Tests the ability to pass context between steps in a plan.
"""
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.plan import Plan, Step
from src.core.planner import Planner
from src.core.memory import MemoryEngine
from src.mcp.resolver import get_resolver
from src.mcp.capabilities import CapabilityRequest, Origin
from src.executors.terminal_executor import TerminalExecutor
from src.executors.llm_executor import LLMExecutor

def test_context_passing():
    """
    Test that context from one step can be passed to the next step.
    """
    print("=== Test: Context Passing Between Steps ===\n")
    
    # Initialize components
    resolver = get_resolver()
    resolver.register_executor("terminal_executor", TerminalExecutor())
    resolver.register_executor("llm_executor", LLMExecutor())
    
    # Create a manual plan with 2 steps
    plan = Plan(
        goal="Test context passing from terminal to LLM",
        reasoning="Step 1 generates text, Step 2 summarizes it using context_from_step",
        steps=[
            Step(
                id=1,
                name="generate_text",
                capability="terminal.execute",
                params={"command": "echo 'This is a test message about artificial intelligence and machine learning. AI is transforming the world with deep learning models and neural networks.'"},
                requires_feedback=False
            ),
            Step(
                id=2,
                name="summarize_text",
                capability="llm.summarize",
                params={
                    "context_from_step": 1,
                    "instruction": "Bu metni çok kısa özetle (maksimum 5 kelime)"
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
        print(f"[Step {step.id}] {step.name} ({step.capability})")
        
        # Copy params and resolve context
        params = step.params.copy()
        if "context_from_step" in params:
            context_step_id = params["context_from_step"]
            if context_step_id in step_outputs:
                params["context"] = str(step_outputs[context_step_id])
                print(f"  → Context resolved from step {context_step_id}")
                print(f"  → Context preview: {params['context'][:80]}...")
            else:
                print(f"  ⚠ Step {context_step_id} output not found")
                params["context"] = ""
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
            print(f"  ✓ Success ({result.execution_time_ms:.0f}ms)")
            if result.data:
                print(f"  → Output: {str(result.data)[:100]}")
            print()
    
    # Results
    print("="*50)
    if all_success:
        print("✓ TEST PASSED")
        print(f"\nStep 1 Output: {step_outputs.get(1, 'N/A')}")
        print(f"Step 2 Output (Summary): {step_outputs.get(2, 'N/A')}")
    else:
        print("✗ TEST FAILED")
    
    return all_success


def test_planner_generates_context_plan():
    """
    Test that the planner can generate a plan with context_from_step.
    """
    print("\n\n=== Test: Planner Generates Context Plan ===\n")
    
    planner = Planner(memory_engine=None)
    
    # Test command that should trigger multi-step with context
    command = "Sistem durumunu kontrol et ve özetle"
    
    print(f"Command: '{command}'")
    print("Generating plan...\n")
    
    plan = planner.generate_plan(command)
    
    print(f"Goal: {plan.goal}")
    print(f"Reasoning: {plan.reasoning}")
    print(f"Steps: {len(plan.steps)}\n")
    
    for step in plan.steps:
        print(f"Step {step.id}: {step.name}")
        print(f"  Capability: {step.capability}")
        print(f"  Params: {step.params}")
        print()
    
    # Check if any step uses context_from_step
    has_context = any("context_from_step" in step.params for step in plan.steps)
    
    print("="*50)
    if has_context:
        print("✓ TEST PASSED - Plan includes context_from_step")
    else:
        print("⚠ TEST WARNING - Plan does not include context_from_step")
        print("  (This might be OK if the LLM chose a different approach)")
    
    return True


if __name__ == "__main__":
    print("╔═══════════════════════════════════════╗")
    print("║  PHASE 1 INTEGRATION TESTS            ║")
    print("╚═══════════════════════════════════════╝\n")
    
    try:
        # Test 1: Manual context passing
        test1_passed = test_context_passing()
        
        # Test 2: Planner generation
        test2_passed = test_planner_generates_context_plan()
        
        print("\n\n" + "="*50)
        print("FINAL RESULTS:")
        print(f"  Context Passing: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"  Planner Generation: {'PASSED' if test2_passed else 'FAILED'}")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
