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
            elif action == "app.list":
                return self._list_apps()
            elif action == "app.info":
                return self._get_app_info(params.get("app_name"))
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
            elif action == "app.switch":
                return self._switch_to_app(params.get("app_name"))
            elif action == "app.cycle":
                return self._cycle_apps()
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

    def _list_apps(self) -> ExecutionResult:
        """List all installed applications on the system"""
        try:
            # Use mdfind to find all applications
            result = subprocess.run(
                ["mdfind", "kMDItemKind == 'Application'"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                app_paths = [path.strip() for path in result.stdout.split('\n') if path.strip()]

                # Alternative approach if mdfind returns no results - scan common directories
                if not app_paths:
                    import glob
                    app_paths = []

                    # Search in common application directories
                    common_dirs = [
                        "/Applications/*.app",
                        "/System/Applications/*.app",
                        "/Applications/Utilities/*.app",
                        os.path.expanduser("~/Applications/*.app")
                    ]

                    for app_dir_pattern in common_dirs:
                        app_paths.extend(glob.glob(app_dir_pattern))

                    # Deduplicate
                    app_paths = list(set(app_paths))

                # Extract just the app names from the paths
                app_names = []
                for app_path in app_paths:
                    app_name = os.path.basename(app_path)
                    # Remove .app extension
                    if app_name.endswith('.app'):
                        app_name = app_name[:-4]
                    app_names.append(app_name)

                # Remove duplicates while preserving order
                unique_apps = list(dict.fromkeys(app_names))

                return ExecutionResult(
                    success=True,
                    data={"applications": unique_apps}
                )
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Failed to list applications: {result.stderr}"
                )
        except Exception as e:
            return ExecutionResult(False, error=f"Failed to list applications: {str(e)}")

    def _get_app_info(self, app_name: str) -> ExecutionResult:
        """Get detailed information about a specific application"""
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")

        try:
            # If app_name doesn't end with .app, add it
            search_name = app_name if app_name.endswith('.app') else f"{app_name}.app"

            # Find the app using mdfind
            find_result = subprocess.run(
                ["mdfind", f"kMDItemDisplayName == '{app_name}' || kMDItemCFBundleIdentifier == '{app_name}'"],
                capture_output=True,
                text=True
            )

            if find_result.returncode == 0 and find_result.stdout.strip():
                app_path = find_result.stdout.strip().split('\n')[0]  # Take the first match
            else:
                # If not found by name, try looking in standard locations
                standard_locations = [
                    f"/Applications/{search_name}",
                    f"/System/Applications/{search_name}",
                    f"/Applications/Utilities/{search_name}",
                    os.path.expanduser(f"~/Applications/{search_name}")
                ]

                app_path = None
                for location in standard_locations:
                    if os.path.exists(location):
                        app_path = location
                        break

                if not app_path:
                    return ExecutionResult(
                        False,
                        error=f"Application '{app_name}' not found"
                    )

            # Get app information using mdls (metadata list)
            info_result = subprocess.run(
                ["mdls", "-raw", "-name", "kMDItemCFBundleIdentifier", "-name", "kMDItemVersion",
                 "-name", "kMDItemShortVersionString", "-name", "kMDItemKind",
                 "-name", "kMDItemLastUsedDate", "-name", "kMDItemDateAdded", app_path],
                capture_output=True,
                text=True
            )

            # Initialize the app info dict with the path
            app_info = {
                'name': app_name,
                'path': app_path
            }

            if info_result.returncode == 0:
                # Parse the metadata
                metadata_lines = info_result.stdout.strip().split('\n')

                # Map the metadata fields to readable names
                metadata_map = {
                    'kMDItemCFBundleIdentifier': 'bundle_id',
                    'kMDItemVersion': 'version',
                    'kMDItemShortVersionString': 'short_version',
                    'kMDItemKind': 'kind',
                    'kMDItemLastUsedDate': 'last_used_date',
                    'kMDItemDateAdded': 'date_added'
                }

                # Process the metadata lines to pair keys with values
                i = 0
                while i < len(metadata_lines):
                    line = metadata_lines[i]
                    if line.startswith('kMDItem'):
                        key = line
                        # Look for the next non-key line as the value
                        j = i + 1
                        while j < len(metadata_lines) and metadata_lines[j].startswith('kMDItem'):
                            j += 1
                        if j < len(metadata_lines):
                            value = metadata_lines[j]
                            readable_key = metadata_map.get(key, key.lower())
                            app_info[readable_key] = value
                    i += 1

                return ExecutionResult(
                    success=True,
                    data={"app_info": app_info}
                )
            else:
                # If mdls fails, try to get basic info from the Info.plist file
                info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
                if os.path.exists(info_plist_path):
                    # Use plutil to read plist information (macOS utility)
                    try:
                        plist_result = subprocess.run(
                            ["plutil", "-extract", "CFBundleIdentifier", "raw", info_plist_path],
                            capture_output=True,
                            text=True
                        )
                        if plist_result.returncode == 0:
                            app_info['bundle_id'] = plist_result.stdout.strip()

                        plist_result = subprocess.run(
                            ["plutil", "-extract", "CFBundleShortVersionString", "raw", info_plist_path],
                            capture_output=True,
                            text=True
                        )
                        if plist_result.returncode == 0:
                            app_info['short_version'] = plist_result.stdout.strip()

                        plist_result = subprocess.run(
                            ["plutil", "-extract", "CFBundleVersion", "raw", info_plist_path],
                            capture_output=True,
                            text=True
                        )
                        if plist_result.returncode == 0:
                            app_info['version'] = plist_result.stdout.strip()

                        plist_result = subprocess.run(
                            ["plutil", "-extract", "CFBundleName", "raw", info_plist_path],
                            capture_output=True,
                            text=True
                        )
                        if plist_result.returncode == 0:
                            app_info['display_name'] = plist_result.stdout.strip()

                    except Exception:
                        # If plutil fails, at least we have the path
                        pass

                return ExecutionResult(
                    success=True,
                    data={"app_info": app_info}
                )

        except Exception as e:
            return ExecutionResult(False, error=f"Failed to get app info for '{app_name}': {str(e)}")

    def _switch_to_app(self, app_name: str) -> ExecutionResult:
        """Switch to an application, bringing it to the front"""
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")

        try:
            # First check if the app is currently running
            check_running = f'''
            tell application "System Events"
                return name of every application process whose visible is true
            end tell
            '''

            result = subprocess.run(["osascript", "-e", check_running], capture_output=True, text=True)

            if app_name not in result.stdout:
                # If the app is not currently visible/running, use activate to bring it to front
                script = f'''
                tell application "{app_name}"
                    activate
                end tell
                '''
            else:
                # If app is running, switch to it by activating
                script = f'''
                tell application "{app_name}"
                    activate
                end tell
                '''

            subprocess.run(["osascript", "-e", script])
            return ExecutionResult(True, f"Switched to {app_name}")

        except Exception as e:
            return ExecutionResult(False, f"Failed to switch to {app_name}: {str(e)}")

    def _cycle_apps(self) -> ExecutionResult:
        """Cycle through running applications, typically using cmd+tab equivalent"""
        try:
            # Get list of running applications
            get_frontmost = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set runningApps to name of every application process whose background only is false
            end tell
            '''

            result = subprocess.run(["osascript", "-e", get_frontmost], capture_output=True, text=True)

            if result.returncode != 0:
                return ExecutionResult(False, f"Failed to get running applications: {result.stderr}")

            # Parse the result to get the frontmost app and other running apps
            lines = result.stdout.strip().split('\n')
            if not lines or len(lines) == 0:
                return ExecutionResult(False, "No running applications found")

            # For cycling apps, we'll simulate Cmd+Tab using AppleScript
            # This brings up the app switcher and moves to the next app
            cycle_script = '''
            tell application "System Events"
                key code 48 using {command down}  -- cmd+tab
            end tell
            '''

            subprocess.run(["osascript", "-e", cycle_script])
            time.sleep(0.2)  # Brief pause to allow the switch to occur

            # Release the keys to complete the cycle
            release_keys = '''
            tell application "System Events"
                key up command
            end tell
            '''

            subprocess.run(["osascript", "-e", release_keys])

            return ExecutionResult(True, "Cycled to next application")

        except Exception as e:
            return ExecutionResult(False, f"Failed to cycle applications: {str(e)}")
