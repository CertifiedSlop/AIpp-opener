"""Async application execution module for AIpp Opener."""

import asyncio
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
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""


class AsyncAppExecutor:
    """Executes applications asynchronously."""

    def __init__(self, use_notifications: bool = True):
        """
        Initialize the executor.

        Args:
            use_notifications: Whether to send system notifications.
        """
        self.use_notifications = use_notifications
        logger.debug("AsyncAppExecutor initialized (notifications=%s)", use_notifications)

    async def execute(
        self,
        executable: str,
        args: Optional[list[str]] = None,
        background: bool = True,
    ) -> ExecutionResult:
        """
        Execute an application asynchronously.

        Args:
            executable: The executable name or path.
            args: Optional additional arguments.
            background: Whether to run in background.

        Returns:
            ExecutionResult with execution status.
        """
        logger.info("Executing: %s (args=%s, background=%s)", executable, args, background)

        # Find the executable
        exec_path = await self._find_executable(executable)
        if not exec_path:
            logger.error("Executable not found: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=executable,
                message=f"Executable not found: {executable}",
            )

        # Build command
        cmd = [exec_path]
        if args:
            cmd.extend(args)

        try:
            if background:
                # Run in background using asyncio.create_subprocess_exec
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    start_new_session=True,
                )
                pid = process.pid

                logger.info("Launched %s in background (PID: %d)", executable, pid)

                if self.use_notifications:
                    await self._send_notification("App Launching", f"Starting {executable}...")

                return ExecutionResult(
                    success=True,
                    app_name=executable,
                    executable=exec_path,
                    message=f"Launched {executable} (PID: {pid})",
                    pid=pid,
                )
            else:
                # Run in foreground with timeout
                logger.debug("Running %s in foreground", executable)
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=60
                    )

                    if process.returncode == 0:
                        logger.info("Foreground execution of %s succeeded", executable)
                        return ExecutionResult(
                            success=True,
                            app_name=executable,
                            executable=exec_path,
                            message=stdout.decode() if stdout else f"Executed {executable}",
                            returncode=process.returncode,
                            stdout=stdout.decode() if stdout else "",
                            stderr=stderr.decode() if stderr else "",
                        )
                    else:
                        logger.error(
                            "Foreground execution of %s failed: %s",
                            executable,
                            stderr.decode() if stderr else "",
                        )
                        return ExecutionResult(
                            success=False,
                            app_name=executable,
                            executable=exec_path,
                            message=stderr.decode() if stderr else f"Command failed with code {process.returncode}",
                            returncode=process.returncode,
                            stdout=stdout.decode() if stdout else "",
                            stderr=stderr.decode() if stderr else "",
                        )

                except asyncio.TimeoutError:
                    logger.error("Command timed out: %s", executable)
                    process.kill()
                    await process.wait()
                    return ExecutionResult(
                        success=False,
                        app_name=executable,
                        executable=exec_path,
                        message="Command timed out",
                        returncode=-1,
                    )

        except FileNotFoundError:
            logger.error("Executable not found: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Executable not found: {executable}",
            )
        except PermissionError:
            logger.error("Permission denied: %s", executable)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Permission denied: {executable}",
            )
        except Exception as e:
            logger.exception("Unexpected error executing %s: %s", executable, e)
            return ExecutionResult(
                success=False,
                app_name=executable,
                executable=exec_path or executable,
                message=f"Error: {str(e)}",
            )

    async def _find_executable(self, name: str) -> Optional[str]:
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

    async def _send_notification(self, title: str, message: str) -> None:
        """Send a system notification asynchronously."""
        logger.debug("Sending notification: %s - %s", title, message)
        try:
            # Try notify-send (Linux)
            process = await asyncio.create_subprocess_exec(
                "notify-send",
                title,
                message,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await process.wait()
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

    async def is_executable(self, name: str) -> bool:
        """
        Check if a name refers to an executable.

        Args:
            name: The executable name.

        Returns:
            True if executable exists.
        """
        return await self._find_executable(name) is not None

    async def execute_with_retry(
        self,
        executable: str,
        args: Optional[list[str]] = None,
        background: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> ExecutionResult:
        """
        Execute an application with retry logic.

        Args:
            executable: The executable name or path.
            args: Optional additional arguments.
            background: Whether to run in background.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            ExecutionResult with execution status.
        """
        last_result = None

        for attempt in range(max_retries):
            result = await self.execute(executable, args, background)

            if result.success:
                return result

            last_result = result

            if attempt < max_retries - 1:
                logger.warning(
                    "Execution failed (attempt %d/%d), retrying in %.1fs...",
                    attempt + 1,
                    max_retries,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)

        return last_result

    async def execute_multiple(
        self,
        apps: list[tuple[str, Optional[list[str]]]],
        delay: float = 0.5,
    ) -> list[ExecutionResult]:
        """
        Execute multiple applications with a delay between each.

        Args:
            apps: List of (executable, args) tuples.
            delay: Delay between launches in seconds.

        Returns:
            List of ExecutionResults.
        """
        results = []

        for i, (executable, args) in enumerate(apps):
            if i > 0:
                await asyncio.sleep(delay)

            result = await self.execute(executable, args, background=True)
            results.append(result)

        return results
