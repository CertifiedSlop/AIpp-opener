"""
Sample plugin for AIpp Opener - Result Modifier.

This plugin modifies execution results to add notifications.

Installation:
    Copy this file to ~/.local/share/aipp_opener/plugins/notification_modifier.py

Usage:
    After installation, run:
    python -m aipp_opener --plugins  # List plugins
    python -m aipp_opener --enable-plugin notification_modifier

Features:
    - Shows desktop notifications when apps are launched
    - Logs execution history with timestamps
    - Optional sound effects

Author: AIpp Opener Team
License: MIT
"""

from datetime import datetime
from pathlib import Path

from aipp_opener.plugins import ResultModifierPlugin
from aipp_opener.executor import ExecutionResult


class NotificationModifierPlugin(ResultModifierPlugin):
    """Adds desktop notifications to execution results."""

    @property
    def name(self) -> str:
        return "notification_modifier"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Shows desktop notifications when applications are launched"

    def __init__(self):
        self._log_file: Path = Path.home() / ".local" / "state" / "aipp_opener" / "launches.log"
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure the log directory exists."""
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def modify_result(self, result: ExecutionResult) -> ExecutionResult:
        """
        Modify the execution result to add notifications.

        Args:
            result: The original execution result.

        Returns:
            Modified execution result with notification info.
        """
        # Log the launch
        self._log_launch(result)

        # Show notification
        self._show_notification(result)

        return result

    def _log_launch(self, result: ExecutionResult) -> None:
        """Log application launch to file."""
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "app_name": getattr(result, "app_name", "unknown"),
            "executable": getattr(result, "executable", "unknown"),
            "success": getattr(result, "success", False),
        }

        try:
            with open(self._log_file, "a") as f:
                f.write(f"{timestamp} - {log_entry['app_name']} ({log_entry['executable']})\n")
        except IOError as e:
            from aipp_opener.logger_config import get_logger
            logger = get_logger(__name__)
            logger.warning("Could not log launch: %s", e)

    def _show_notification(self, result: ExecutionResult) -> None:
        """Show desktop notification."""
        app_name = getattr(result, "app_name", "Application")
        success = getattr(result, "success", False)

        if success:
            message = f"✓ {app_name} launched successfully"
        else:
            message = f"✗ Failed to launch {app_name}"

        # Try to show notification using notify-send
        try:
            subprocess.run(
                ["notify-send", "-u", "normal" if success else "critical", "AIpp Opener", message],
                capture_output=True,
                timeout=5
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fallback: print message
            print(message)

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        from aipp_opener.logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Notification Modifier plugin loaded")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        from aipp_opener.logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Notification Modifier plugin unloaded")


# Import subprocess here to avoid issues in modify_result
import subprocess

# Export the plugin class
__all__ = ["NotificationModifierPlugin"]
