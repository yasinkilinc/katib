"""
MacOS MCP Tool Server
Exposes macOS capabilities as MCP tools.
"""
import json
import subprocess
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

# Tool Registry - Stateless tool definitions
TOOLS: Dict[str, ToolDefinition] = {
    "open_application": ToolDefinition(
        name="open_application",
        description="Open a macOS application by name",
        inputSchema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Name of the application to open"}
            },
            "required": ["app_name"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"}
            }
        }
    ),
    "close_application": ToolDefinition(
        name="close_application",
        description="Close a running macOS application",
        inputSchema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Name of the application to close"}
            },
            "required": ["app_name"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        }
    ),
    "set_volume": ToolDefinition(
        name="set_volume",
        description="Set the system volume level (0-100)",
        inputSchema={
            "type": "object",
            "properties": {
                "level": {"type": "integer", "minimum": 0, "maximum": 100}
            },
            "required": ["level"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "new_level": {"type": "integer"}
            }
        }
    ),
    "web_navigate": ToolDefinition(
        name="web_navigate",
        description="Open a URL in the default browser",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"}
            },
            "required": ["url"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        }
    ),
    "web_search": ToolDefinition(
        name="web_search",
        description="Search the web using Google or YouTube",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "platform": {"type": "string", "enum": ["google", "youtube"], "default": "google"}
            },
            "required": ["query"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        }
    ),
    "web_close_tab": ToolDefinition(
        name="web_close_tab",
        description="Close a browser tab. If 'title_match' is provided, closes matching tabs in Safari/Chrome. Otherwise closes active tab.",
        inputSchema={
            "type": "object",
            "properties": {
                "title_match": {"type": "string", "description": "Partial title to match (e.g. 'Sahibinden')"}
            }
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"}
            }
        },
        metadata={"unsafe": False, "requiresConfirmation": True} # Closing things usually warrants confirmation if specific
    ),
    "tts_speak": ToolDefinition(
        name="tts_speak",
        description="Speak text using macOS text-to-speech",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "default": "Yelda"}
            },
            "required": ["text"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        }
    ),
    "lock_screen": ToolDefinition(
        name="lock_screen",
        description="Lock the screen / put display to sleep",
        inputSchema={
            "type": "object",
            "properties": {}
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        },
        metadata={"fallback": False, "unsafe": False, "requiresConfirmation": True}
    ),
    "ui_click": ToolDefinition(
        name="ui_click",
        description="Click at specific screen coordinates or current position",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate (optional)"},
                "y": {"type": "integer", "description": "Y coordinate (optional)"},
                "clicks": {"type": "integer", "default": 1},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
            }
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        },
        metadata={"fallback": True, "unsafe": True, "requiresConfirmation": True}
    ),
    "ui_type": ToolDefinition(
        name="ui_type",
        description="Type text at current cursor position",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
                "interval": {"type": "number", "default": 0.05}
            },
            "required": ["text"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        },
        metadata={"fallback": True, "unsafe": True, "requiresConfirmation": True}
    ),
    "ui_press_key": ToolDefinition(
        name="ui_press_key",
        description="Press a keyboard key with optional modifiers",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name (e.g. 'enter', 'esc', 'a')"},
                "modifiers": {"type": "array", "items": {"type": "string"}, "description": "Modifiers like 'command', 'shift'"}
            },
            "required": ["key"]
        },
        outputSchema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"}
            }
        },
        metadata={"fallback": True, "unsafe": True, "requiresConfirmation": True}
    ),
}


class MacOSToolServer:
    """
    MCP Tool Server for macOS.
    Handles tool.list and tool.call requests.
    """
    
    def __init__(self):
        self.tools = TOOLS
    
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
            return {
                "jsonrpc": "2.0",
                "result": {"success": False, "error": f"Unknown tool: {name}"}
            }
        
        # Dispatch to handler
        handler = getattr(self, f"_handle_{name}", None)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "result": {"success": False, "error": f"No handler for tool: {name}"}
            }
        
        try:
            result = handler(**arguments)
            return {
                "jsonrpc": "2.0",
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "result": {"success": False, "error": str(e)}
            }
    
    # --- Tool Handlers (Stateless) ---
    
    def _handle_open_application(self, app_name: str) -> Dict[str, Any]:
        subprocess.run(f"open -a '{app_name}'", shell=True)
        return {"success": True, "message": f"Opened {app_name}"}
    
    def _handle_close_application(self, app_name: str) -> Dict[str, Any]:
        subprocess.run(f"pkill -x '{app_name}'", shell=True)
        return {"success": True}
    
    def _handle_set_volume(self, level: int) -> Dict[str, Any]:
        subprocess.run(f"osascript -e 'set volume output volume {level}'", shell=True)
        return {"success": True, "new_level": level}
    
    def _handle_web_navigate(self, url: str) -> Dict[str, Any]:
        if not url.startswith("http"):
            url = f"https://{url}"
        subprocess.run(f"open '{url}'", shell=True)
        return {"success": True}
    
    def _handle_web_search(self, query: str, platform: str = "google") -> Dict[str, Any]:
        if platform == "youtube":
            url = f"https://www.youtube.com/results?search_query={query}"
        else:
            url = f"https://www.google.com/search?q={query}"
        subprocess.run(f"open '{url}'", shell=True)
        return {"success": True}

    def _handle_web_close_tab(self, title_match: str = None) -> Dict[str, Any]:
        """
        Close browser tabs using AppleScript or shortcut.
        Supports Safari and Google Chrome.
        Checks both TITLE and URL for the match.
        """
        if not title_match:
            # Fallback: Just press Cmd+W to close active tab
            from tools.ui import ui_press_key
            result = ui_press_key("w", ["command"])
            return {"success": result["success"], "message": "Closed active tab via shortcut"}
        
        # AppleScript to close matching tabs in Safari (Title or URL)
        safari_script = f"""
        tell application "Safari"
            if it is running then
                set windowList to every window
                repeat with aWindow in windowList
                    set tabList to every tab of aWindow
                    repeat with aTab in tabList
                        if (name of aTab contains "{title_match}") or (URL of aTab contains "{title_match}") then
                            close aTab
                        end if
                    end repeat
                end repeat
            end if
        end tell
        """
        
        # AppleScript to close matching tabs in Chrome (Title or URL)
        chrome_script = f"""
        tell application "Google Chrome"
            if it is running then
                set windowList to every window
                repeat with aWindow in windowList
                    set tabList to every tab of aWindow
                    repeat with aTab in tabList
                        if (title of aTab contains "{title_match}") or (URL of aTab contains "{title_match}") then
                            close aTab
                        end if
                    end repeat
                end repeat
            end if
        end tell
        """
        
        try:
            # Run for both browsers safely
            subprocess.run(["osascript", "-e", safari_script], check=False)
            subprocess.run(["osascript", "-e", chrome_script], check=False)
            return {"success": True, "message": f"Closed tabs matching '{title_match}' in Title or URL"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_tts_speak(self, text: str, voice: str = "Yelda") -> Dict[str, Any]:
        subprocess.run(['say', '-v', voice, text])
        return {"success": True}
    
    def _handle_lock_screen(self) -> Dict[str, Any]:
        subprocess.run("pmset displaysleepnow", shell=True)
        return {"success": True}

    # --- UI Automation Handlers ---
    
    def _handle_ui_click(self, x: int = None, y: int = None, clicks: int = 1, button: str = 'left') -> Dict[str, Any]:
        from tools.ui import ui_click
        return ui_click(x, y, clicks, button)
    
    def _handle_ui_type(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        from tools.ui import ui_type
        return ui_type(text, interval)
    
    def _handle_ui_press_key(self, key: str, modifiers: list = None) -> Dict[str, Any]:
        from tools.ui import ui_press_key
        return ui_press_key(key, modifiers)


# Singleton instance
_server: Optional[MacOSToolServer] = None

def get_macos_server() -> MacOSToolServer:
    global _server
    if _server is None:
        _server = MacOSToolServer()
    return _server
