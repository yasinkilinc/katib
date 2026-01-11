"""
Agent Core - The reasoning component that selects tools.
Does NOT know about macOS or any specific platform.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .policy import get_policy_engine, PolicyDecision
from .mcp_client import MCPClient, Tool, ToolResult
from .memory import get_memory_manager, MemoryManager

@dataclass
class AgentResponse:
    """Response from the agent"""
    success: bool
    tool_calls: List[Dict[str, Any]]
    results: List[ToolResult]
    message: Optional[str] = None

class Agent:
    """
    The core reasoning agent.
    - Receives user intent
    - Uses LLM to decide which tools to call
    - Validates with Policy Engine
    - Executes tools via MCP Client
    - Records to memory (Selective)
    - Handles failures with retry
    """
    
    def __init__(self, llm, mcp_client: MCPClient, memory: MemoryManager = None, confirmation_callback=None):
        self.llm = llm
        self.client = mcp_client
        self.memory = memory or get_memory_manager()
        self.policy = get_policy_engine()
        self.max_retries = 2
        self.confirmation_callback = confirmation_callback
    
    def process(self, user_intent: str) -> AgentResponse:
        # ... (same as before) ...
        # 1. Record intent
        self.memory.record_intent(user_intent)
        
        # 2. Get tools
        tools_for_llm = self.client.get_tools_for_llm()
        
        # 3. Get context
        context = self.memory.get_session_context()
        
        # 4. LLM decides
        tool_decisions = self.llm.decide_tools(user_intent, tools_for_llm, context)
        
        # 5. Execute with Policy Check
        results = []
        for decision in tool_decisions:
            tool_name = decision.get("name", "")
            arguments = decision.get("parameters", {})
            
            # --- Policy Evaluation Step ---
            tool_def = self.client.get_tool(tool_name)
            if not tool_def:
                results.append(ToolResult(success=False, error=f"Unknown tool: {tool_name}"))
                break
                
            policy_result = self.policy.evaluate(tool_name, arguments, tool_def.metadata)
            
            if policy_result.decision == PolicyDecision.DENY:
                # DENY -> Record failure with explanation
                error_msg = f"Policy DENIED: {policy_result.reason}"
                results.append(ToolResult(success=False, error=error_msg))
                
                # Selective Memory: Record Denial
                self.memory.record_tool_call(
                    tool_name=tool_name, 
                    arguments=arguments, 
                    success=False, 
                    execution_time_ms=0, 
                    error=error_msg,
                    is_important=True # Security denials are important
                )
                print(f"[X] Blocked by Policy: {policy_result.reason}")
                break # Stop execution chain security violation
                
            elif policy_result.decision == PolicyDecision.CONFIRM:
                # CONFIRM -> Ask UI
                approved = False
                if self.confirmation_callback:
                    approved = self.confirmation_callback(tool_name, arguments, reason=policy_result.reason)
                else:
                    # No UI to ask -> Deny
                    policy_result.reason += " (No confirmation callback provided)"
                
                if not approved:
                     error_msg = f"User DENIED: {policy_result.reason}"
                     results.append(ToolResult(success=False, error=error_msg))
                     
                     self.memory.record_tool_call(
                        tool_name=tool_name,
                        arguments=arguments,
                        success=False,
                        execution_time_ms=0,
                        error=error_msg,
                        is_important=True
                     )
                     break
            
            # --- Execution Step (if ALLOW or CONFIRM+APPROVED) ---
            result = self._execute_tool(tool_name, arguments)
            results.append(result)
            
            # Selective Memory: Record valid execution
            self.memory.record_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
                error=result.error,
                # Simple heuristic for importance: modifications or errors are important
                is_important=not result.success or tool_def.metadata.get("unsafe", False)
            )
            
            if not result.success:
                break
        
        # 6. Return response
        all_success = all(r.success for r in results) if results else False
        return AgentResponse(
            success=all_success,
            tool_calls=tool_decisions,
            results=results
        )
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool with simple retry logic"""
        last_result = None
        for attempt in range(self.max_retries + 1):
            result = self.client.call_tool(tool_name, arguments)
            if result.success:
                return result
            last_result = result
            if attempt < self.max_retries:
                print(f"[!] Retry {attempt + 1}/{self.max_retries} for {tool_name}")
        return last_result
    
    def get_available_tools(self) -> List[Tool]:
        """Get list of available tools (for debugging/display)"""
        return self.client.list_tools()
    
    def save_session(self):
        """Save current session to persistent storage"""
        self.memory.save_session()
