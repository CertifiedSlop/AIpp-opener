"""Tests for async executor module (Phase 8)."""

import unittest
import asyncio
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
        self.assertEqual(result.pid, 1234)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "output")


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
            self.assertIsNotNone(result.pid)

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

    def test_execute_returncode(self):
        """Test async execution returncode."""
        async def run_test():
            result = await self.executor.execute("true", background=False)
            self.assertEqual(result.returncode, 0)

        asyncio.run(run_test())

    def test_execute_failure_returncode(self):
        """Test async execution failure returncode."""
        async def run_test():
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
            path = await self.executor._find_executable("/usr/bin/echo")
            if path:  # May not exist on all systems
                self.assertTrue(path.endswith("echo"))

        asyncio.run(run_test())


class TestAsyncAppExecutorNotifications(unittest.TestCase):
    """Tests for AsyncAppExecutor notification features."""

    def test_send_notification(self):
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

    def test_execute_with_spaces_in_args(self):
        """Test executing command with spaces in args."""
        async def run_test():
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


if __name__ == "__main__":
    unittest.main()
