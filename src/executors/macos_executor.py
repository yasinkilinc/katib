import subprocess
import os
import platform
import time
from typing import Dict, Any
from .base_executor import BaseExecutor, ExecutionResult

class MacOSExecutor(BaseExecutor):
    def execute(self, action: str, params: Dict[str, Any]) -> ExecutionResult:
        try:
            if action == "app.open":
                return self._open_app(params.get("app_name"))
            elif action == "app.close":
                return self._close_app(params.get("app_name"))
            elif action == "app.focus":
                return self._activate_app(params.get("app_name"))
            elif action == "system.volume":
                return self._set_volume(params.get("level"))
            elif action == "tts.speak":
                return self._speak(params.get("text"))
            elif action == "web.navigate":
                # Simple fallback if Windsurf unavailable
                return self._open_url(params.get("url"))
            elif action == "web.close_tab":
                 # Fallback attempt via AppleScript
                return self._close_browser_tab(params.get("title_match"))
            else:
                 return ExecutionResult(success=False, error=f"Unknown MacOS action: {action}")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    def _open_app(self, app_name: str) -> ExecutionResult:
        if not app_name: return ExecutionResult(False, error="Missing app_name")
        subprocess.run(["open", "-a", app_name])
        return ExecutionResult(True, f"Opened {app_name}")

    def _close_app(self, app_name: str) -> ExecutionResult:
        if not app_name: return ExecutionResult(False, error="Missing app_name")
        script = f'quit app "{app_name}"'
        subprocess.run(["osascript", "-e", script])
        return ExecutionResult(True, f"Closed {app_name}")
        
    def _activate_app(self, app_name: str) -> ExecutionResult:
        if not app_name: return ExecutionResult(False, error="Missing app_name")
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        return ExecutionResult(True, f"Focused {app_name}")

    def _set_volume(self, level: int) -> ExecutionResult:
        # level 0-100
        if level is None: return ExecutionResult(False, error="Missing level")
        # macOS volume is 0-7 usually, or 0-100 output volume
        vol = f"set volume output volume {level}"
        subprocess.run(["osascript", "-e", vol])
        return ExecutionResult(True, f"Volume set to {level}")

    def _speak(self, text: str) -> ExecutionResult:
        if not text: return ExecutionResult(False, error="Missing text")
        subprocess.run(["say", text])
        return ExecutionResult(True, "Spoken")

    def _open_url(self, url: str) -> ExecutionResult:
        if not url: return ExecutionResult(False, error="Missing url")
        if not url.startswith("http"): url = "https://" + url
        subprocess.run(["open", url])
        return ExecutionResult(True, f"Opened {url}")
        
    def _close_browser_tab(self, title_match: str) -> ExecutionResult:
        if not title_match: return ExecutionResult(False, error="Missing title_match")
        
        # Try Chrome first (since user specifically uses it)
        chrome_script = f'''
        tell application "Google Chrome"
            repeat with w in windows
                set i to 1
                repeat with t in tabs of w
                    if title of t contains "{title_match}" then
                        close t
                        return "closed"
                    end if
                    set i to i + 1
                end repeat
            end repeat
        end tell
        '''
        
        # Try Safari if Chrome script fails or returns nothing relevant
        safari_script = f'''
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    if name of t contains "{title_match}" then
                        close t
                        return "closed"
                    end if
                end repeat
            end repeat
        end tell
        '''

        try:
            # Attempt Chrome
            res = subprocess.run(["osascript", "-e", chrome_script], capture_output=True, text=True)
            if "closed" in res.stdout:
                return ExecutionResult(True, f"Closed Chrome tab matching '{title_match}'")
                
            # Attempt Safari
            res = subprocess.run(["osascript", "-e", safari_script], capture_output=True, text=True)
            if "closed" in res.stdout:
                return ExecutionResult(True, f"Closed Safari tab matching '{title_match}'")
                
            return ExecutionResult(False, f"No tab found matching '{title_match}' in Chrome or Safari")
            
        except Exception as e:
             return ExecutionResult(False, f"Browser control failed: {str(e)}")
