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
            elif action == "app.launch_with_file":
                return self._launch_app_with_file(
                    params.get("app_name"),
                    params.get("file_path")
                )
            elif action == "document.open":
                return self._open_document(params.get("file_path"))
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
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")

        try:
            # Check if app exists by attempting to find its path
            result = subprocess.run(["mdfind", f"kMDItemCFBundleIdentifier == '{app_name}' || kMDItemDisplayName == '{app_name}'"],
                                  capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                # App found by name or bundle ID, launch it
                subprocess.run(["open", "-a", app_name])
                return ExecutionResult(True, f"Successfully opened {app_name}")
            else:
                # Try with full path in case it's a full application path
                result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return ExecutionResult(True, f"Successfully opened {app_name}")
                else:
                    return ExecutionResult(False, f"Could not find application: {app_name}")
        except Exception as e:
            return ExecutionResult(False, f"Failed to open {app_name}: {str(e)}")

    def _launch_app_with_file(self, app_name: str, file_path: str) -> ExecutionResult:
        """Launch an application with a specific file"""
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")
        if not file_path:
            return ExecutionResult(False, error="Missing file_path")

        # Verify the file exists
        if not os.path.exists(file_path):
            return ExecutionResult(False, error=f"File does not exist: {file_path}")

        try:
            result = subprocess.run(["open", "-a", app_name, file_path], capture_output=True, text=True)
            if result.returncode == 0:
                return ExecutionResult(True, f"Opened {file_path} with {app_name}")
            else:
                return ExecutionResult(False, f"Failed to open {file_path} with {app_name}: {result.stderr}")
        except Exception as e:
            return ExecutionResult(False, f"Failed to open {file_path} with {app_name}: {str(e)}")

    def _open_document(self, file_path: str) -> ExecutionResult:
        """Open a document using the default application"""
        if not file_path:
            return ExecutionResult(False, error="Missing file_path")

        # Verify the file exists
        if not os.path.exists(file_path):
            return ExecutionResult(False, error=f"File does not exist: {file_path}")

        try:
            result = subprocess.run(["open", file_path], capture_output=True, text=True)
            if result.returncode == 0:
                return ExecutionResult(True, f"Opened document {file_path}")
            else:
                return ExecutionResult(False, f"Failed to open document {file_path}: {result.stderr}")
        except Exception as e:
            return ExecutionResult(False, f"Failed to open document {file_path}: {str(e)}")

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
