"""
MCP Client - Connects to Tool Servers and manages tool calls.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

@dataclass
class Tool:
    """Represents an available tool from a server"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    outputSchema: Dict[str, Any]
    metadata: Dict[str, Any]
    server_name: str

@dataclass
class ToolResult:
    """Result of a tool call"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class MCPClient:
    """
    MCP Client that connects to tool servers.
    Platform-agnostic - doesn't know about macOS or any specific server.
    """
    
    def __init__(self):
        self.servers: Dict[str, Any] = {}  # name -> server instance
        self.tools_cache: Dict[str, Tool] = {}
    
    def register_server(self, name: str, server: Any):
        """Register a tool server"""
        self.servers[name] = server
        # Refresh tool cache
        self._refresh_tools(name, server)
    
    def _refresh_tools(self, server_name: str, server: Any):
        """Fetch tools from a server and cache them"""
        response = server.handle_list()
        tools = response.get("result", {}).get("tools", [])
        
        for tool_data in tools:
            tool = Tool(
                name=tool_data["name"],
                description=tool_data["description"],
                inputSchema=tool_data["inputSchema"],
                outputSchema=tool_data.get("outputSchema", {}),
                metadata=tool_data.get("metadata", {}),
                server_name=server_name
            )
            self.tools_cache[tool.name] = tool
    
    def list_tools(self) -> List[Tool]:
        """List all available tools from all servers"""
        return list(self.tools_cache.values())
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a specific tool by name"""
        return self.tools_cache.get(name)
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Call a tool and return the result"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        
        server = self.servers.get(tool.server_name)
        if not server:
            return ToolResult(success=False, error=f"Server not found: {tool.server_name}")
        
        start_time = time.time()
        
        try:
            response = server.handle_call(name, arguments)
            result_data = response.get("result", {})
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=result_data.get("success", False),
                output=result_data,
                error=result_data.get("error"),
                execution_time_ms=execution_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tool descriptions formatted for LLM consumption"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
            for tool in self.tools_cache.values()
        ]


# Singleton
_client: Optional[MCPClient] = None

def get_mcp_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
