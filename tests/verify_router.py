import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.executors.router import ActionRouter

def test_router():
    print("Testing ActionRouter...")
    router = ActionRouter()
    
    plan = [
        {
            "step_id": 1,
            "action": "speak",
            "executor": "macos_executor",
            "parameters": {"text": "Router testing complete"}
        },
        {
            "step_id": 2,
            "action": "run_shell",
            "executor": "terminal_executor",
            "parameters": {"command": "echo 'Terminal Executor working'"}
        }
    ]
    
    result = router.execute_plan(plan)
    if result:
        print("Router verification SUCCESS")
    else:
        print("Router verification FAILED")

if __name__ == "__main__":
    test_router()
