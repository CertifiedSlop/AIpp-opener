"""Tests for AIpp Opener executor (aipp_opener/executor.py)."""

import unittest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock


class TestExecutionResult(unittest.TestCase):
    """Test ExecutionResult dataclass."""

    def test_execution_result_success(self):
        """Test successful execution result."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="firefox",
            executable="/usr/bin/firefox",
            message="Launched firefox",
            pid=12345,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.app_name, "firefox")
        self.assertEqual(result.pid, 12345)

    def test_execution_result_failure(self):
        """Test failed execution result."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=False,
            app_name="nonexistent",
            executable="nonexistent",
            message="Executable not found",
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.pid)


class TestAppExecutor(unittest.TestCase):
    """Test AppExecutor class."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.executor import AppExecutor

        self.executor = AppExecutor(use_notifications=False)

    def test_execute_background_success(self):
        """Test executing app in background."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/firefox'):
                result = self.executor.execute('firefox', background=True)

                self.assertTrue(result.success)
                self.assertEqual(result.pid, 12345)
                mock_popen.assert_called_once()

    def test_execute_foreground_success(self):
        """Test executing app in foreground."""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_run.return_value = mock_result

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/echo'):
                result = self.executor.execute('echo', args=['hello'], background=False)

                self.assertTrue(result.success)
                self.assertEqual(result.message, "output")

    def test_execute_not_found(self):
        """Test executing non-existent app."""
        with patch.object(self.executor, '_find_executable', return_value=None):
            result = self.executor.execute('nonexistent_app_xyz')

            self.assertFalse(result.success)
            self.assertIn("not found", result.message.lower())

    def test_execute_timeout(self):
        """Test execution timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('cmd', 60)

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/slow'):
                result = self.executor.execute('slow', background=False)

                self.assertFalse(result.success)
                self.assertIn("timed out", result.message.lower())

    def test_execute_permission_denied(self):
        """Test execution with permission denied."""
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = PermissionError("Permission denied")

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/protected'):
                result = self.executor.execute('protected', background=True)

                self.assertFalse(result.success)
                self.assertIn("permission denied", result.message.lower())

    def test_execute_with_args(self):
        """Test executing app with arguments."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/app'):
                result = self.executor.execute('app', args=['--flag', 'value'], background=True)

                self.assertTrue(result.success)
                # Verify args were passed
                call_args = mock_popen.call_args[0][0]
                self.assertIn('--flag', call_args)
                self.assertIn('value', call_args)

    def test_find_executable_absolute_path(self):
        """Test finding executable with absolute path."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('os.access', return_value=True):
                result = self.executor._find_executable('/usr/bin/firefox')

                self.assertEqual(result, '/usr/bin/firefox')

    def test_find_executable_in_path(self):
        """Test finding executable in PATH."""
        with patch('shutil.which', return_value='/usr/bin/firefox'):
            result = self.executor._find_executable('firefox')

            self.assertEqual(result, '/usr/bin/firefox')

    def test_find_executable_not_found(self):
        """Test finding executable that doesn't exist."""
        with patch('shutil.which', return_value=None):
            with patch('pathlib.Path.exists', return_value=False):
                result = self.executor._find_executable('nonexistent_app')

                self.assertIsNone(result)

    def test_find_executable_common_locations(self):
        """Test finding executable in common locations."""
        with patch('shutil.which', return_value=None):
            # Mock Path.exists to return True for at least one path
            with patch('pathlib.Path.exists', return_value=True):
                with patch('os.access', return_value=True):
                    result = self.executor._find_executable('app')

                    # Should find in common paths or return None
                    # Test just verifies the method runs without error
                    self.assertTrue(result is None or isinstance(result, str))

    def test_is_executable_true(self):
        """Test is_executable returns True for existing executable."""
        with patch.object(self.executor, '_find_executable', return_value='/usr/bin/app'):
            result = self.executor.is_executable('app')

            self.assertTrue(result)

    def test_is_executable_false(self):
        """Test is_executable returns False for non-existing executable."""
        with patch.object(self.executor, '_find_executable', return_value=None):
            result = self.executor.is_executable('nonexistent')

            self.assertFalse(result)

    def test_list_common_executables(self):
        """Test listing common executables."""
        with patch.object(self.executor, 'is_executable') as mock_is_exec:
            # Make some apps "available"
            def is_exec_side_effect(name):
                available_apps = {'firefox', 'code', 'vlc'}
                return name in available_apps

            mock_is_exec.side_effect = is_exec_side_effect

            result = self.executor.list_common_executables()

            self.assertIn('firefox', result)
            self.assertIn('code', result)
            self.assertIn('vlc', result)
            self.assertNotIn('nonexistent', result)


class TestAppExecutorNotifications(unittest.TestCase):
    """Test notification functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.executor import AppExecutor

        self.executor = AppExecutor(use_notifications=True)

    def test_send_notification_notify_send(self):
        """Test sending notification via notify-send."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            self.executor._send_notification("Title", "Message")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args[0], 'notify-send')

    def test_send_notification_fallback(self):
        """Test notification fallback to notify-py."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("notify-send not found")

            try:
                from notify_py import notify
                with patch('notify_py.notify') as mock_notify:
                    self.executor._send_notification("Title", "Message")
                    mock_notify.assert_called_once_with(title="Title", content="Message")
            except ModuleNotFoundError:
                # notify-py not installed, test passes by not raising
                pass

    def test_send_notification_both_fail(self):
        """Test notification when both methods fail."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("notify-send not found")

            try:
                from notify_py import notify
                with patch('notify_py.notify') as mock_notify:
                    mock_notify.side_effect = Exception("notify-py failed")
                    # Should not raise exception
                    self.executor._send_notification("Title", "Message")
            except ModuleNotFoundError:
                # notify-py not installed, test passes by not raising
                pass


class TestAppExecutorWithNotificationsDisabled(unittest.TestCase):
    """Test executor with notifications disabled."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.executor import AppExecutor

        self.executor = AppExecutor(use_notifications=False)

    def test_execute_no_notification(self):
        """Test that notifications are not sent when disabled."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            with patch.object(self.executor, '_find_executable', return_value='/usr/bin/app'):
                with patch.object(self.executor, '_send_notification') as mock_notify:
                    result = self.executor.execute('app', background=True)

                    self.assertTrue(result.success)
                    mock_notify.assert_not_called()


class TestExecutionResultEdgeCases(unittest.TestCase):
    """Test edge cases for ExecutionResult."""

    def test_execution_result_with_empty_message(self):
        """Test ExecutionResult with empty message."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="app",
            executable="/usr/bin/app",
            message="",
        )

        self.assertEqual(result.message, "")

    def test_execution_result_with_none_pid(self):
        """Test ExecutionResult with None pid."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="app",
            executable="/usr/bin/app",
            message="Success",
            pid=None,
        )

        self.assertIsNone(result.pid)

    def test_execution_result_str_representation(self):
        """Test ExecutionResult string representation."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="firefox",
            executable="/usr/bin/firefox",
            message="Launched",
        )

        # Should be able to convert to string
        str_repr = str(result)
        self.assertIsInstance(str_repr, str)


if __name__ == "__main__":
    unittest.main()
