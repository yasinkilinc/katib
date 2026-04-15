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
            elif action == "process.list":
                return self._list_processes()
            elif action == "process.find":
                return self._find_process(params.get("process_name"))
            elif action == "process.kill":
                return self._kill_process(params.get("pid", params.get("process_name")))
            elif action == "app.running":
                return self._is_app_running(params.get("app_name"))
            elif action == "app.state":
                return self._get_app_state(params.get("app_name"))
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
        """Open a document using the default application via AppleScript"""
        if not file_path:
            return ExecutionResult(False, error="Missing file_path")

        # Verify the file exists
        if not os.path.exists(file_path):
            return ExecutionResult(False, error=f"File does not exist: {file_path}")

        try:
            # Convert file path to POSIX format for AppleScript
            posix_path = os.path.abspath(file_path)

            # Use AppleScript to open the document with the default application
            script = f'''
            try
                tell application "Finder"
                    open POSIX file "{posix_path}"
                end tell
                return "success"
            on error errorMessage
                -- If Finder fails, try using the open command via AppleScript
                try
                    do shell script "open '{posix_path}'"
                    return "success"
                on error shell_error
                    return "error: " & errorMessage & " | shell error: " & shell_error
                end try
            end try
            '''

            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0 and "success" in result.stdout:
                return ExecutionResult(True, f"Opened document {file_path}")
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return ExecutionResult(False, f"Failed to open document {file_path}: {error_msg}")
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

    def _list_processes(self) -> ExecutionResult:
        """List all running processes on the system"""
        try:
            # Use ps command to get detailed process information
            result = subprocess.run([
                "ps", "-axo", "pid,ppid,uid,stat,pcpu,pmem,comm,command"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                headers = lines[0].strip().split()
                processes = []

                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(None, 7)  # Split into 8 parts maximum
                        if len(parts) >= 8:
                            try:
                                proc_info = {
                                    'pid': int(parts[0]) if parts[0].isdigit() else 0,
                                    'ppid': int(parts[1]) if parts[1].isdigit() else 0,
                                    'uid': int(parts[2]) if parts[2].isdigit() else 0,
                                    'status': parts[3],
                                    'cpu_percent': float(parts[4]) if parts[4] not in ['-', 'N/A'] else 0.0,
                                    'mem_percent': float(parts[5]) if parts[5] not in ['-', 'N/A'] else 0.0,
                                    'command': parts[6],
                                    'full_command': parts[7]
                                }
                                processes.append(proc_info)
                            except (ValueError, IndexError):
                                # Skip malformed lines
                                continue

                return ExecutionResult(
                    success=True,
                    data={"processes": processes}
                )
            else:
                return ExecutionResult(
                    False,
                    error=f"Failed to list processes: {result.stderr}"
                )
        except Exception as e:
            return ExecutionResult(False, error=f"Failed to list processes: {str(e)}")

    def _find_process(self, process_name: str) -> ExecutionResult:
        """Find processes matching a specific name"""
        if not process_name:
            return ExecutionResult(False, error="Missing process_name")

        try:
            # Use pgrep to find processes by name
            result = subprocess.run([
                "pgrep", "-f", process_name
            ], capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                pids = [pid.strip() for pid in result.stdout.split('\n') if pid.strip()]

                # Get detailed info for each found process
                detailed_processes = []
                for pid_str in pids:
                    if not pid_str.isdigit():
                        continue

                    pid = int(pid_str)

                    # Get process info using ps
                    ps_result = subprocess.run([
                        "ps", "-o", "pid,ppid,uid,stat,pcpu,pmem,comm,command", "-p", str(pid)
                    ], capture_output=True, text=True)

                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split(None, 7)  # Skip header, split command
                            if len(parts) >= 8:
                                try:
                                    proc_info = {
                                        'pid': int(parts[0]),
                                        'ppid': int(parts[1]),
                                        'uid': int(parts[2]),
                                        'status': parts[3],
                                        'cpu_percent': float(parts[4]) if parts[4] not in ['-', 'N/A'] else 0.0,
                                        'mem_percent': float(parts[5]) if parts[5] not in ['-', 'N/A'] else 0.0,
                                        'command': parts[6],
                                        'full_command': parts[7]
                                    }
                                    detailed_processes.append(proc_info)
                                except (ValueError, IndexError):
                                    # Skip malformed lines
                                    continue

                return ExecutionResult(
                    success=True,
                    data={
                        "process_name": process_name,
                        "matches": detailed_processes
                    }
                )
            else:
                return ExecutionResult(
                    True,
                    data={
                        "process_name": process_name,
                        "matches": [],
                        "message": f"No processes found matching '{process_name}'"
                    }
                )
        except Exception as e:
            return ExecutionResult(False, error=f"Failed to find process '{process_name}': {str(e)}")

    def _kill_process(self, pid_or_name) -> ExecutionResult:
        """Kill a process by PID or name"""
        if not pid_or_name:
            return ExecutionResult(False, error="Missing pid or process_name")

        try:
            # Determine if input is a PID (numeric) or process name
            if isinstance(pid_or_name, str) and pid_or_name.isdigit():
                pid = int(pid_or_name)
                # Kill by PID
                result = subprocess.run(["kill", str(pid)], capture_output=True, text=True)
                if result.returncode == 0:
                    return ExecutionResult(True, f"Process {pid} killed successfully")
                else:
                    return ExecutionResult(False, f"Failed to kill process {pid}: {result.stderr}")
            else:
                # Kill by process name
                process_name = pid_or_name
                result = subprocess.run(["pkill", "-f", process_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return ExecutionResult(True, f"Process(es) matching '{process_name}' killed successfully")
                else:
                    return ExecutionResult(False, f"Failed to kill process matching '{process_name}': {result.stderr}")
        except Exception as e:
            return ExecutionResult(False, error=f"Failed to kill process: {str(e)}")

    def _is_app_running(self, app_name: str) -> ExecutionResult:
        """Check if a specific application is currently running"""
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")

        try:
            # Use AppleScript to check if the application is running
            script = f'''
            try
                tell application "System Events"
                    set appName to "{app_name}"
                    set isRunning to (name of every process) contains appName
                    return isRunning
                end tell
            on error
                return false
            end try
            '''

            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

            if result.returncode == 0:
                output = result.stdout.strip()
                is_running = "true" in output.lower()
                status = "running" if is_running else "not running"

                return ExecutionResult(
                    success=True,
                    data={
                        "app_name": app_name,
                        "is_running": is_running,
                        "status": status
                    }
                )
            else:
                # If AppleScript fails, try using pgrep as a fallback
                pgrep_result = subprocess.run(["pgrep", "-f", app_name], capture_output=True, text=True)
                if pgrep_result.returncode == 0 and pgrep_result.stdout.strip():
                    is_running = True
                    status = "running"
                else:
                    is_running = False
                    status = "not running"

                return ExecutionResult(
                    success=True,
                    data={
                        "app_name": app_name,
                        "is_running": is_running,
                        "status": status
                    }
                )
        except Exception as e:
            return ExecutionResult(False, error=f"Failed to check if app is running '{app_name}': {str(e)}")

    def _get_app_state(self, app_name: str) -> ExecutionResult:
        """Get detailed state information about a running application"""
        if not app_name:
            return ExecutionResult(False, error="Missing app_name")

        try:
            # First check if the app is running using the same approach as _is_app_running
            script = f'''
            try
                tell application "System Events"
                    set appName to "{app_name}"
                    set isRunning to (name of every process) contains appName
                    return isRunning
                end tell
            on error
                return false
            end try
            '''

            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

            if result.returncode == 0 and "true" in result.stdout.lower():
                # App is running, get detailed state info with proper error handling
                state_script = f'''
                try
                    tell application "System Events"
                        set appName to "{app_name}"
                        set appProcess to process appName
                        set isVisible to visible of appProcess
                        set isFrontmost to frontmost of appProcess
                        set appWindows to count of windows of appProcess
                    on error
                        set isVisible to missing value
                        set isFrontmost to missing value
                        set appWindows to 0
                    end try
                    return {{isVisible, isFrontmost, appWindows}}
                end try
                '''

                state_result = subprocess.run(["osascript", "-e", state_script], capture_output=True, text=True)

                # Also get the process ID via pgrep for additional system-level information
                pid_result = subprocess.run(["pgrep", "-f", app_name], capture_output=True, text=True)
                pid = None
                if pid_result.returncode == 0 and pid_result.stdout.strip():
                    try:
                        pid = int(pid_result.stdout.strip().split()[0])
                    except ValueError:
                        pass

                app_state = {
                    "app_name": app_name,
                    "is_running": True,
                    "is_visible": None,
                    "is_frontmost": None,
                    "window_count": None,
                    "pid": pid
                }

                # Parse the AppleScript result if successful
                if state_result.returncode == 0 and state_result.stdout.strip():
                    try:
                        # Extract values from AppleScript result
                        output = state_result.stdout.strip()
                        # Output format is usually something like "true, false, 5"
                        if "," in output:
                            parts = output.split(",")
                            if len(parts) >= 3:
                                app_state["is_visible"] = "true" in parts[0].lower()
                                app_state["is_frontmost"] = "true" in parts[1].lower()
                                app_state["window_count"] = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                    except:
                        pass  # Use defaults if parsing fails

                # Get process resource usage if PID is available
                if pid:
                    try:
                        ps_result = subprocess.run([
                            "ps", "-o", "pcpu,pmem", "-p", str(pid)
                        ], capture_output=True, text=True)

                        if ps_result.returncode == 0:
                            lines = ps_result.stdout.strip().split('\n')
                            if len(lines) > 1:
                                cpu_mem = lines[1].split()
                                if len(cpu_mem) >= 2:
                                    app_state["cpu_percent"] = float(cpu_mem[0]) if cpu_mem[0] not in ['-', 'N/A'] else 0.0
                                    app_state["memory_percent"] = float(cpu_mem[1]) if cpu_mem[1] not in ['-', 'N/A'] else 0.0
                    except:
                        pass  # Ignore PS errors

                return ExecutionResult(
                    success=True,
                    data={"app_state": app_state}
                )
            else:
                # App is not running
                app_state = {
                    "app_name": app_name,
                    "is_running": False,
                    "error": f"Application '{app_name}' is not currently running"
                }

                return ExecutionResult(
                    success=False,
                    data={"app_state": app_state}
                )

        except Exception as e:
            return ExecutionResult(False, error=f"Failed to get app state for '{app_name}': {str(e)}")
