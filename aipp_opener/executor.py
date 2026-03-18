"""Application execution module for AIpp Opener."""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


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
        logger.debug("AppExecutor initialized (notifications=%s)", use_notifications)

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
        logger.info("Executing: %s (args=%s, background=%s)", executable, args, background)

        # Find the executable
        exec_path = self._find_executable(executable)
        if not exec_path:
            logger.error("Executable not found: %s", executable)
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

                logger.info("Launched %s in background (PID: %d)", executable, pid)

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
                logger.debug("Running %s in foreground", executable)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    logger.info("Foreground execution of %s succeeded", executable)
                    return ExecutionResult(
                        success=True,
                        app_name=executable,
                        executable=exec_path,
                        message=result.stdout or f"Executed {executable}"
                    )
                else:
                    logger.error("Foreground execution of %s failed: %s", executable, result.stderr)
                    return ExecutionResult(
                        success=False,
                        app_name=executable,
                        executable=exec_path,
                        message=result.stderr or f"Command failed with code {result.returncode}"
                    )

        except subprocess.TimeoutExpired:
            logger.error("Command timed out: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path,
                message="Command timed out"
            )
        except FileNotFoundError:
            logger.error("Executable not found: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Executable not found: {executable}"
            )
        except PermissionError:
            logger.error("Permission denied: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Permission denied: {executable}"
            )
        except Exception as e:
            logger.exception("Unexpected error executing %s: %s", executable, e)
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
        logger.debug("Searching for executable: %s", name)

        # If it's already a path, check if it exists
        if "/" in name:
            path = Path(name)
            if path.exists() and os.access(path, os.X_OK):
                logger.debug("Found executable at path: %s", path)
                return str(path.absolute())
            logger.debug("Path exists but not executable: %s", path)
            return None

        # Use shutil.which to find in PATH
        exec_path = shutil.which(name)
        if exec_path:
            logger.debug("Found executable in PATH: %s", exec_path)
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
                logger.debug("Found executable in common path: %s", path)
                return str(path)

        logger.debug("Executable not found: %s", name)
        return None

    def _send_notification(self, title: str, message: str) -> None:
        """Send a system notification."""
        logger.debug("Sending notification: %s - %s", title, message)
        try:
            # Try notify-send (Linux)
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                timeout=5
            )
            logger.debug("Notification sent via notify-send")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug("notify-send not available: %s", e)
            try:
                # Try using notify-py as fallback
                from notify_py import notify
                notify(title=title, content=message)
                logger.debug("Notification sent via notify-py")
            except Exception as e:
                logger.warning("Failed to send notification: %s", e)

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
