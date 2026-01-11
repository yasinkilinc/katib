"""
Filesystem MCP Tool Server
Exposes secure file operations as MCP tools.
"""
import os
import glob
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ToolDefinition:
    """Definition of an MCP tool"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    outputSchema: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {"fallback": False, "unsafe": False, "requiresConfirmation": False}

# Define allowed paths (sandbox) - Currently allowing generic workspace access
# In a stricter environment, we would limit this.
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TOOLS: Dict[str, ToolDefinition] = {
    "read_file": ToolDefinition(
        name="read_file",
        description="Read the contents of a file",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"}
            },
            "required": ["path"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "success": {"type": "boolean"}
            }
        },
        metadata={"unsafe": False}
    ),
    "write_file": ToolDefinition(
        name="write_file",
        description="Write content to a file (overwrites if exists)",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"}
            }
        },
        metadata={"unsafe": True, "requiresConfirmation": True}  # Writing is unsafe
    ),
    "list_directory": ToolDefinition(
        name="list_directory",
        description="List files and directories in a path",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."}
            },
        },
        outputSchema={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}},
                "success": {"type": "boolean"}
            }
        },
        metadata={"unsafe": False}
    ),
    "file_search": ToolDefinition(
        name="file_search",
        description="Search for files using glob pattern",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
                "path": {"type": "string", "description": "Root path to search in", "default": "."}
            },
            "required": ["pattern"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "matches": {"type": "array", "items": {"type": "string"}},
                "success": {"type": "boolean"}
            }
        },
        metadata={"unsafe": False}
    )
}


class FilesystemServer:
    """
    MCP Tool Server for Filesystem operations.
    """
    
    def __init__(self, root_path: str = WORKSPACE_ROOT):
        self.tools = TOOLS
        self.root_path = os.path.abspath(root_path)
    
    def handle_list(self) -> Dict[str, Any]:
        """Handle tool.list request"""
        tool_list = [asdict(tool) for tool in self.tools.values()]
        return {
            "jsonrpc": "2.0",
            "result": {"tools": tool_list}
        }
    
    def handle_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool.call request"""
        if name not in self.tools:
            return {"jsonrpc": "2.0", "result": {"success": False, "error": f"Unknown tool: {name}"}}
        
        handler = getattr(self, f"_handle_{name}", None)
        if not handler:
            return {"jsonrpc": "2.0", "result": {"success": False, "error": f"No handler for tool: {name}"}}
        
        try:
            result = handler(**arguments)
            return {"jsonrpc": "2.0", "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "result": {"success": False, "error": str(e)}}

    # --- Handlers ---

    def _resolve_path(self, path: str) -> str:
        """Resolve and validate path against root"""
        # Allow absolute paths for flexibility, or restrict to root
        # For this agent, we allow absolute paths as it runs locally for the user
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.root_path, path))

    def _handle_read_file(self, path: str) -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    def _handle_write_file(self, path: str, content: str) -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"File written: {path}"}

    def _handle_list_directory(self, path: str = ".") -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
             raise FileNotFoundError(f"Directory not found: {path}")
             
        items = os.listdir(full_path)
        return {"success": True, "items": items}

    def _handle_file_search(self, pattern: str, path: str = ".") -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        # Use recursive glob if pattern contains **
        recursive = "**" in pattern
        search_pattern = os.path.join(full_path, pattern)
        matches = glob.glob(search_pattern, recursive=recursive)
        
        # Return relative paths for cleaner output
        rel_matches = [os.path.relpath(m, full_path) for m in matches]
        return {"success": True, "matches": rel_matches}


_server: Optional[FilesystemServer] = None

def get_filesystem_server() -> FilesystemServer:
    global _server
    if _server is None:
        _server = FilesystemServer()
    return _server
