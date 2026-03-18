"""Application execution module for AIpp Opener."""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of an application execution."""
    
    success: bool
    app_name: str
    executable: str
    message: str
    pid: Optional[int] = None


class AppExecutor:
    """Executes applications on the system."""
    
    def __init__(self, use_notifications: bool = True):
        """
        Initialize the executor.
        
        Args:
            use_notifications: Whether to send system notifications.
        """
        self.use_notifications = use_notifications
    
    def execute(
        self,
        executable: str,
        args: Optional[list[str]] = None,
        background: bool = True,
    ) -> ExecutionResult:
        """
        Execute an application.
        
        Args:
            executable: The executable name or path.
            args: Optional additional arguments.
            background: Whether to run in background.
            
        Returns:
            ExecutionResult with execution status.
        """
        # Find the executable
        exec_path = self._find_executable(executable)
        if not exec_path:
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=executable,
                message=f"Executable not found: {executable}"
            )
        
        # Build command
        cmd = [exec_path]
        if args:
            cmd.extend(args)
        
        try:
            if background:
                # Run in background
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                pid = process.pid
                
                if self.use_notifications:
                    self._send_notification("App Launching", f"Starting {executable}...")
                
                return ExecutionResult(
                    success=True,
                    app_name=executable,
                    executable=exec_path,
                    message=f"Launched {executable} (PID: {pid})",
                    pid=pid
                )
            else:
                # Run in foreground
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    return ExecutionResult(
                        success=True,
                        app_name=executable,
                        executable=exec_path,
                        message=result.stdout or f"Executed {executable}"
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        app_name=executable,
                        executable=exec_path,
                        message=result.stderr or f"Command failed with code {result.returncode}"
                    )
                    
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path,
                message="Command timed out"
            )
        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Executable not found: {executable}"
            )
        except PermissionError:
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Permission denied: {executable}"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Error: {str(e)}"
            )
    
    def _find_executable(self, name: str) -> Optional[str]:
        """
        Find the full path to an executable.
        
        Args:
            name: The executable name or path.
            
        Returns:
            Full path if found, None otherwise.
        """
        # If it's already a path, check if it exists
        if "/" in name:
            path = Path(name)
            if path.exists() and os.access(path, os.X_OK):
                return str(path.absolute())
            return None
        
        # Use shutil.which to find in PATH
        exec_path = shutil.which(name)
        if exec_path:
            return exec_path
        
        # Check common locations
        common_paths = [
            Path("/usr/bin") / name,
            Path("/usr/local/bin") / name,
            Path("/bin") / name,
            Path("/usr/games") / name,
            Path.home() / ".local/bin" / name,
            Path.home() / ".nix-profile/bin" / name,
        ]
        
        for path in common_paths:
            if path.exists() and os.access(path, os.X_OK):
                return str(path)
        
        return None
    
    def _send_notification(self, title: str, message: str) -> None:
        """Send a system notification."""
        try:
            # Try notify-send (Linux)
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                timeout=5
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                # Try using notify-py as fallback
                from notify_py import notify
                notify(title=title, content=message)
            except Exception:
                pass
    
    def is_executable(self, name: str) -> bool:
        """
        Check if a name refers to an executable.
        
        Args:
            name: The executable name.
            
        Returns:
            True if executable exists.
        """
        return self._find_executable(name) is not None
    
    def list_common_executables(self) -> list[str]:
        """
        List common GUI application executables.
        
        Returns:
            List of executable names found in PATH.
        """
        common_apps = [
            # Browsers
            "firefox", "chrome", "chromium", "brave", "opera", "vivaldi",
            # Editors/IDEs
            "code", "code-insiders", "sublime-text", "atom", "gedit", "kate",
            "vim", "nvim", "emacs", "nano",
            # Terminal
            "gnome-terminal", "konsole", "alacritty", "kitty", "wezterm", "foot",
            # Media
            "vlc", "mpv", "rhythmbox", "spotify", "audacious",
            # Office
            "libreoffice", "writer", "calc", "impress", "evolution", "thunderbird",
            # Graphics
            "gimp", "inkscape", "eog", "krita", "blender",
            # Communication
            "discord", "slack", "zoom", "teams", "telegram-desktop", "signal-desktop",
            # File managers
            "nautilus", "dolphin", "thunar", "pcmanfm", "ranger",
            # System
            "settings", "gnome-control-center", "systemsettings",
            # Games/Launchers
            "steam", "lutris", "heroic",
            # Other
            "obs", "obs-studio", "docker", "postman", "slack",
        ]
        
        found = []
        for app in common_apps:
            if self.is_executable(app):
                found.append(app)
        
        return found
