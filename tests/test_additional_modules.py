"""Tests for additional modules (Phase 6E)."""

import unittest
from unittest.mock import patch, MagicMock


class TestSetupWizard(unittest.TestCase):
    """Tests for setup wizard module."""

    def test_wizard_init(self):
        """Test setup wizard initialization."""
        from aipp_opener.setup_wizard import SetupWizard
        
        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()
                self.assertIsNotNone(wizard)
                self.assertIsNotNone(wizard.config)
                self.assertIsNotNone(wizard.nlp)

    def test_wizard_methods_exist(self):
        """Test setup wizard has required methods."""
        from aipp_opener.setup_wizard import SetupWizard
        
        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()
                
                self.assertTrue(hasattr(wizard, 'run'))
                self.assertTrue(hasattr(wizard, '_configure_ai_provider'))
                self.assertTrue(hasattr(wizard, '_configure_features'))

    @patch('aipp_opener.setup_wizard.ConfigManager')
    @patch('aipp_opener.setup_wizard.NLPProcessor')
    def test_wizard_get_input_default(self, mock_nlp, mock_config):
        """Test _get_input method with default."""
        from aipp_opener.setup_wizard import SetupWizard
        
        wizard = SetupWizard()
        
        with patch('builtins.input', return_value=''):
            result = wizard._get_input("Test prompt", default="default_value")
            self.assertEqual(result, "default_value")

    @patch('aipp_opener.setup_wizard.ConfigManager')
    @patch('aipp_opener.setup_wizard.NLPProcessor')
    def test_wizard_get_input_custom(self, mock_nlp, mock_config):
        """Test _get_input method with custom input."""
        from aipp_opener.setup_wizard import SetupWizard
        
        wizard = SetupWizard()
        
        with patch('builtins.input', return_value='custom_value'):
            result = wizard._get_input("Test prompt", default="default")
            self.assertEqual(result, "custom_value")


class TestAppCategorizerExtended(unittest.TestCase):
    """Extended tests for app categorizer."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.categories import AppCategorizer
        self.categorizer = AppCategorizer()

    def test_categorize_browser_apps(self):
        """Test categorizing browser applications."""
        browsers = ["firefox", "chrome", "chromium", "brave", "vivaldi"]
        for browser in browsers:
            category = self.categorizer.categorize(browser)
            self.assertEqual(category.value, "browser", f"{browser} should be browser")

    def test_categorize_editor_apps(self):
        """Test categorizing editor applications."""
        editors = ["gedit", "kate", "vim", "nvim", "emacs", "nano"]
        for editor in editors:
            category = self.categorizer.categorize(editor)
            self.assertEqual(category.value, "editor", f"{editor} should be editor")

    def test_categorize_ide_apps(self):
        """Test categorizing IDE applications."""
        ides = ["code", "pycharm", "intellij", "webstorm", "eclipse"]
        for ide in ides:
            category = self.categorizer.categorize(ide)
            self.assertEqual(category.value, "ide", f"{ide} should be ide")

    def test_categorize_media_apps(self):
        """Test categorizing media applications."""
        media = ["vlc", "mpv", "rhythmbox", "spotify"]
        for app in media:
            category = self.categorizer.categorize(app)
            self.assertIn(category.value, ["media", "video", "audio"], f"{app} should be media-related")

    def test_categorize_development_apps(self):
        """Test categorizing development applications."""
        dev = ["terminal", "git", "docker"]
        for app in dev:
            category = self.categorizer.categorize(app)
            self.assertIn(category.value, ["development", "terminal", "system"], f"{app} should be dev-related")

    def test_categorize_with_desktop_categories(self):
        """Test categorizing with desktop file categories."""
        category = self.categorizer.categorize("unknown-app", ["AudioVideo"])
        self.assertEqual(category.value, "media")

        category = self.categorizer.categorize("unknown-app", ["Graphics"])
        self.assertEqual(category.value, "graphics")

        category = self.categorizer.categorize("unknown-app", ["Office"])
        self.assertEqual(category.value, "office")

    def test_categorize_unknown_app(self):
        """Test categorizing unknown application."""
        category = self.categorizer.categorize("random-unknown-app-xyz")
        self.assertEqual(category.value, "other")

    def test_categorize_case_insensitive(self):
        """Test categorizing is case insensitive."""
        category1 = self.categorizer.categorize("Firefox")
        category2 = self.categorizer.categorize("FIREFOX")
        category3 = self.categorizer.categorize("firefox")
        
        self.assertEqual(category1.value, category2.value)
        self.assertEqual(category2.value, category3.value)
        self.assertEqual(category1.value, "browser")

    def test_filter_by_category(self):
        """Test filtering apps by category."""
        from aipp_opener.categories import AppCategory
        from aipp_opener.detectors.base import AppInfo
        
        apps = [
            AppInfo(name="firefox", executable="/usr/bin/firefox", categories=["browser"]),
            AppInfo(name="code", executable="/usr/bin/code", categories=["ide"]),
            AppInfo(name="vlc", executable="/usr/bin/vlc", categories=["media"]),
        ]
        
        result = self.categorizer.filter_by_category(apps, AppCategory.BROWSER)
        self.assertIsInstance(result, list)

    def test_get_category_counts(self):
        """Test getting category counts."""
        from aipp_opener.detectors.base import AppInfo
        
        apps = [
            AppInfo(name="firefox", executable="/usr/bin/firefox", categories=["browser"]),
            AppInfo(name="chrome", executable="/usr/bin/chrome", categories=["browser"]),
            AppInfo(name="code", executable="/usr/bin/code", categories=["ide"]),
        ]
        
        counts = self.categorizer.get_category_counts(apps)
        self.assertIsInstance(counts, dict)
        self.assertGreater(len(counts), 0)

    def test_get_categories_summary(self):
        """Test getting categories summary."""
        from aipp_opener.detectors.base import AppInfo
        
        apps = [
            AppInfo(name="firefox", executable="/usr/bin/firefox", categories=["browser"]),
            AppInfo(name="code", executable="/usr/bin/code", categories=["ide"]),
        ]
        
        summary = self.categorizer.get_categories_summary(apps)
        self.assertIsInstance(summary, list)


class TestHistoryExtended(unittest.TestCase):
    """Extended tests for history module."""

    def test_history_record_and_get(self):
        """Test recording and getting history."""
        from aipp_opener.history import HistoryManager
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            history = HistoryManager(history_file=temp_file)
            
            history.record("firefox", "firefox", "/usr/bin/firefox")
            history.record("firefox", "firefox", "/usr/bin/firefox")
            history.record("code", "code", "/usr/bin/code")
            
            frequent = history.get_frequent_apps(5)
            self.assertIsInstance(frequent, list)
            self.assertGreater(len(frequent), 0)
            
            top_app = frequent[0]
            self.assertEqual(top_app['count'], 2)
        finally:
            temp_file.unlink(missing_ok=True)

    def test_history_clear(self):
        """Test clearing history."""
        from aipp_opener.history import HistoryManager
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            history = HistoryManager(history_file=temp_file)
            history.record("test", "test", "/usr/bin/test")
            history.clear()
            
            frequent = history.get_frequent_apps(5)
            self.assertEqual(len(frequent), 0)
        finally:
            temp_file.unlink(missing_ok=True)


class TestIconsExtended(unittest.TestCase):
    """Extended tests for icons module."""

    def test_icon_finder_find_icon(self):
        """Test finding icons."""
        from aipp_opener.icons import IconFinder
        
        finder = IconFinder()
        
        # find_icon requires app_executable parameter
        icon = finder.find_icon("firefox", "/usr/bin/firefox")
        self.assertIsNotNone(icon)
        self.assertTrue(hasattr(icon, 'name') or hasattr(icon, 'path'))

    def test_icon_finder_methods_exist(self):
        """Test icon finder has required methods."""
        from aipp_opener.icons import IconFinder

        finder = IconFinder()
        self.assertTrue(hasattr(finder, 'find_icon'))
        self.assertTrue(hasattr(finder, '_find_from_desktop'))


class TestExecutorExtended(unittest.TestCase):
    """Extended tests for executor module."""

    def test_execute_success(self):
        """Test executing successful command."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        result = executor.execute("true")
        
        self.assertTrue(result.success)
        self.assertEqual(result.app_name, "true")

    def test_execute_failure(self):
        """Test executing failing command."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        result = executor.execute("nonexistent_command_xyz")
        
        self.assertFalse(result.success)

    def test_execute_with_args(self):
        """Test executing command with arguments."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        result = executor.execute("echo", args=["hello"])
        
        self.assertTrue(result.success)

    def test_execute_background(self):
        """Test executing command in background."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        result = executor.execute("true", background=True)
        
        self.assertTrue(result.success)

    def test_find_executable(self):
        """Test finding executable."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        path = executor._find_executable("echo")
        
        self.assertIsNotNone(path)
        self.assertTrue(len(path) > 0)

    def test_find_executable_not_found(self):
        """Test finding non-existent executable."""
        from aipp_opener.executor import AppExecutor
        
        executor = AppExecutor(use_notifications=False)
        path = executor._find_executable("nonexistent_xyz_123")
        
        self.assertIsNone(path)


if __name__ == "__main__":
    unittest.main()
