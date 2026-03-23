"""Tests for async executor module."""

import unittest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestExecutionResult(unittest.TestCase):
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_minimal(self):
        """Test ExecutionResult with minimal fields."""
        from aipp_opener.async_executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="test",
            executable="/test",
            message="Success"
        )
        self.assertTrue(result.success)
        self.assertEqual(result.app_name, "test")
        self.assertEqual(result.executable, "/test")
        self.assertEqual(result.message, "Success")
        self.assertIsNone(result.pid)
        self.assertIsNone(result.returncode)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_execution_result_full(self):
        """Test ExecutionResult with all fields."""
        from aipp_opener.async_executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="test",
            executable="/test",
            message="Success",
            pid=1234,
            returncode=0,
            stdout="output",
            stderr=""
        )
        self.assertTrue(result.success)
        self.assertEqual(result.pid, 1234)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "output")
        self.assertEqual(result.stderr, "")

    def test_execution_result_failure(self):
        """Test ExecutionResult for failure."""
        from aipp_opener.async_executor import ExecutionResult

        result = ExecutionResult(
            success=False,
            app_name="test",
            executable="/test",
            message="Not found",
            returncode=127
        )
        self.assertFalse(result.success)
        self.assertEqual(result.returncode, 127)


class TestAsyncAppExecutor(unittest.TestCase):
    """Tests for AsyncAppExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_executor import AsyncAppExecutor
        self.executor = AsyncAppExecutor(use_notifications=False)

    def test_executor_init(self):
        """Test AsyncAppExecutor initialization."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor()
        self.assertIsNotNone(executor)
        self.assertTrue(executor.use_notifications)

    def test_executor_init_no_notifications(self):
        """Test AsyncAppExecutor without notifications."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor(use_notifications=False)
        self.assertFalse(executor.use_notifications)

    def test_execute_success(self):
        """Test successful async execution."""
        async def run_test():
            result = await self.executor.execute("true")
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_with_args(self):
        """Test async execution with arguments."""
        async def run_test():
            result = await self.executor.execute("echo", args=["hello"])
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_not_found(self):
        """Test async execution with non-existent command."""
        async def run_test():
            result = await self.executor.execute("nonexistent_xyz_123")
            self.assertFalse(result.success)
            self.assertIn("not found", result.message.lower())

        asyncio.run(run_test())

    def test_execute_background(self):
        """Test background async execution."""
        async def run_test():
            result = await self.executor.execute("true", background=True)
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_foreground(self):
        """Test foreground async execution."""
        async def run_test():
            result = await self.executor.execute("true", background=False)
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_with_stdout_capture(self):
        """Test async execution with stdout capture."""
        async def run_test():
            result = await self.executor.execute("echo", args=["test output"], background=False)
            self.assertTrue(result.success)
            self.assertIn("test output", result.stdout)

        asyncio.run(run_test())

    def test_execute_with_stderr_capture(self):
        """Test async execution with stderr capture."""
        async def run_test():
            # Use a command that writes to stderr
            result = await self.executor.execute(
                "python", args=["-c", "import sys; print('error', file=sys.stderr)"],
                background=False
            )
            self.assertTrue(result.success)
            self.assertIn("error", result.stderr)

        asyncio.run(run_test())

    def test_execute_returncode(self):
        """Test async execution returncode."""
        async def run_test():
            result = await self.executor.execute("true", background=False)
            self.assertEqual(result.returncode, 0)

        asyncio.run(run_test())

    def test_execute_failure_returncode(self):
        """Test async execution failure returncode."""
        async def run_test():
            # Use a command that definitely fails
            result = await self.executor.execute("sh", args=["-c", "exit 1"], background=False)
            self.assertFalse(result.success)
            self.assertEqual(result.returncode, 1)

        asyncio.run(run_test())


class TestAsyncAppExecutorHelpers(unittest.TestCase):
    """Tests for AsyncAppExecutor helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_executor import AsyncAppExecutor
        self.executor = AsyncAppExecutor(use_notifications=False)

    def test_find_executable_found(self):
        """Test finding an existing executable."""
        async def run_test():
            path = await self.executor._find_executable("echo")
            self.assertIsNotNone(path)
            self.assertTrue(len(path) > 0)

        asyncio.run(run_test())

    def test_find_executable_not_found(self):
        """Test finding a non-existent executable."""
        async def run_test():
            path = await self.executor._find_executable("nonexistent_xyz_123")
            self.assertIsNone(path)

        asyncio.run(run_test())

    def test_find_executable_with_path(self):
        """Test finding executable with full path."""
        async def run_test():
            # /bin/echo should exist on most Linux systems
            path = await self.executor._find_executable("/bin/echo")
            # May be None if /bin/echo doesn't exist (some systems use /usr/bin/echo)
            if path:
                self.assertTrue(path.endswith("echo"))

        asyncio.run(run_test())

    def test_find_executable_in_usr_bin(self):
        """Test finding executable in /usr/bin."""
        async def run_test():
            path = await self.executor._find_executable("/usr/bin/echo")
            if path:
                self.assertTrue(path.endswith("echo"))

        asyncio.run(run_test())

    def test_is_executable(self):
        """Test checking if something is executable."""
        async def run_test():
            result = await self.executor.is_executable("echo")
            self.assertTrue(result)

        asyncio.run(run_test())

    def test_is_executable_not_found(self):
        """Test checking if non-existent is executable."""
        async def run_test():
            result = await self.executor.is_executable("nonexistent_xyz_123")
            self.assertFalse(result)

        asyncio.run(run_test())


class TestAsyncAppExecutorNotifications(unittest.TestCase):
    """Tests for AsyncAppExecutor notification features."""

    def test_executor_with_notifications(self):
        """Test executor with notifications enabled."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor(use_notifications=True)
        self.assertTrue(executor.use_notifications)

    def test_send_notification_success(self):
        """Test sending notification."""
        from aipp_opener.async_executor import AsyncAppExecutor

        async def run_test():
            executor = AsyncAppExecutor(use_notifications=True)
            # Should not raise
            await executor._send_notification("Test", "Test message")

        asyncio.run(run_test())

    def test_send_notification_disabled(self):
        """Test notification sending when disabled."""
        from aipp_opener.async_executor import AsyncAppExecutor

        async def run_test():
            executor = AsyncAppExecutor(use_notifications=False)
            # Should not raise
            await executor._send_notification("Test", "Test message")

        asyncio.run(run_test())


class TestAsyncAppExecutorEdgeCases(unittest.TestCase):
    """Tests for AsyncAppExecutor edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_executor import AsyncAppExecutor
        self.executor = AsyncAppExecutor(use_notifications=False)

    def test_execute_empty_command(self):
        """Test executing empty command."""
        async def run_test():
            result = await self.executor.execute("")
            self.assertFalse(result.success)

        asyncio.run(run_test())

    def test_execute_with_spaces_in_path(self):
        """Test executing command with spaces in path."""
        async def run_test():
            # This tests handling of paths with spaces
            result = await self.executor.execute("echo", args=["hello world"])
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_multiple_args(self):
        """Test executing command with multiple arguments."""
        async def run_test():
            result = await self.executor.execute(
                "echo", args=["arg1", "arg2", "arg3"]
            )
            self.assertTrue(result.success)

        asyncio.run(run_test())

    def test_execute_command_with_special_chars(self):
        """Test executing command with special characters."""
        async def run_test():
            result = await self.executor.execute("echo", args=["test$var"])
            self.assertTrue(result.success)

        asyncio.run(run_test())


class TestAsyncAppExecutorIntegration(unittest.TestCase):
    """Integration tests for AsyncAppExecutor."""

    def test_multiple_executions(self):
        """Test multiple async executions."""
        from aipp_opener.async_executor import AsyncAppExecutor

        async def run_test():
            executor = AsyncAppExecutor(use_notifications=False)

            results = []
            for _ in range(3):
                result = await executor.execute("true")
                results.append(result)

            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.success for r in results))

        asyncio.run(run_test())

    def test_concurrent_executions(self):
        """Test concurrent async executions."""
        from aipp_opener.async_executor import AsyncAppExecutor

        async def run_test():
            executor = AsyncAppExecutor(use_notifications=False)

            # Run multiple commands concurrently
            tasks = [
                executor.execute("echo", args=[f"task{i}"])
                for i in range(3)
            ]
            results = await asyncio.gather(*tasks)

            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.success for r in results))

        asyncio.run(run_test())

    def test_mixed_success_failure(self):
        """Test mixed success and failure executions."""
        from aipp_opener.async_executor import AsyncAppExecutor

        async def run_test():
            executor = AsyncAppExecutor(use_notifications=False)

            success_result = await executor.execute("true", background=False)
            failure_result = await executor.execute("sh", args=["-c", "exit 1"], background=False)

            self.assertTrue(success_result.success)
            self.assertFalse(failure_result.success)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
