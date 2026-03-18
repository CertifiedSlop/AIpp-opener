"""Comprehensive tests for AIpp Opener."""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestAppInfo(unittest.TestCase):
    """Test AppInfo dataclass."""

    def test_app_info_creation(self):
        """Test creating AppInfo object."""
        from aipp_opener.detectors.base import AppInfo

        app = AppInfo(name="firefox", executable="/usr/bin/firefox", display_name="Firefox Browser")

        self.assertEqual(app.name, "firefox")
        self.assertEqual(app.executable, "/usr/bin/firefox")
        self.assertEqual(app.display_name, "Firefox Browser")

    def test_app_info_default_display_name(self):
        """Test AppInfo default display name."""
        from aipp_opener.detectors.base import AppInfo

        app = AppInfo(name="test", executable="/usr/bin/test")
        self.assertEqual(app.display_name, "test")

    def test_app_info_default_categories(self):
        """Test AppInfo default categories."""
        from aipp_opener.detectors.base import AppInfo

        app = AppInfo(name="test", executable="/usr/bin/test")
        self.assertEqual(app.categories, [])


class TestAppCategories(unittest.TestCase):
    """Test application categorization."""

    def setUp(self):
        from aipp_opener.categories import AppCategorizer

        self.categorizer = AppCategorizer()

    def test_browser_categorization(self):
        """Test browser app categorization."""
        from aipp_opener.categories import AppCategory

        browsers = ["firefox", "chrome", "chromium", "brave"]
        for browser in browsers:
            category = self.categorizer.categorize(browser)
            self.assertEqual(category, AppCategory.BROWSER, f"Failed for {browser}")

    def test_editor_categorization(self):
        """Test editor app categorization."""
        from aipp_opener.categories import AppCategory

        editors = ["gedit", "kate", "vim", "emacs"]
        for editor in editors:
            category = self.categorizer.categorize(editor)
            self.assertEqual(category, AppCategory.EDITOR, f"Failed for {editor}")

    def test_ide_categorization(self):
        """Test IDE app categorization."""
        from aipp_opener.categories import AppCategory

        ides = ["code", "pycharm", "intellij"]
        for ide in ides:
            category = self.categorizer.categorize(ide)
            self.assertEqual(category, AppCategory.IDE, f"Failed for {ide}")

    def test_media_categorization(self):
        """Test media app categorization."""
        from aipp_opener.categories import AppCategory

        media = ["vlc", "mpv", "rhythmbox", "spotify"]
        for app in media:
            category = self.categorizer.categorize(app)
            self.assertIn(category, [AppCategory.MEDIA, AppCategory.AUDIO], f"Failed for {app}")

    def test_graphics_categorization(self):
        """Test graphics app categorization."""
        from aipp_opener.categories import AppCategory

        graphics = ["gimp", "inkscape", "krita", "blender"]
        for app in graphics:
            category = self.categorizer.categorize(app)
            self.assertEqual(category, AppCategory.GRAPHICS, f"Failed for {app}")


class TestNLPProcessor(unittest.TestCase):
    """Test NLP processing functionality."""

    def setUp(self):
        from aipp_opener.ai.nlp import NLPProcessor

        self.nlp = NLPProcessor()

    def test_extract_app_intent_simple(self):
        """Test extracting app name from simple command."""
        result = self.nlp.extract_app_intent("open firefox")
        self.assertEqual(result, "firefox")

    def test_extract_app_intent_with_launch(self):
        """Test extracting app name with 'launch' verb."""
        result = self.nlp.extract_app_intent("launch code")
        self.assertIn("code", result.lower())

    def test_extract_app_intent_with_start(self):
        """Test extracting app name with 'start' verb."""
        result = self.nlp.extract_app_intent("start spotify")
        self.assertEqual(result, "spotify")

    def test_extract_app_intent_polite(self):
        """Test extracting app name from polite request."""
        result = self.nlp.extract_app_intent("please open firefox")
        self.assertEqual(result, "firefox")

    def test_normalize_app_name(self):
        """Test app name normalization."""
        self.assertEqual(self.nlp.normalize_app_name("VS Code"), "code")
        self.assertEqual(self.nlp.normalize_app_name("Visual Studio Code"), "code")
        self.assertEqual(self.nlp.normalize_app_name("Google Chrome"), "chrome")

    def test_categorize_request_open(self):
        """Test categorizing open requests."""
        result = self.nlp.categorize_request("open firefox")
        self.assertEqual(result, "open")

    def test_categorize_request_suggest(self):
        """Test categorizing suggestion requests."""
        result = self.nlp.categorize_request("what browser should I use")
        self.assertEqual(result, "suggest")

    def test_find_best_match(self):
        """Test fuzzy matching."""
        candidates = ["firefox", "chrome", "chromium", "brave"]
        matches = self.nlp.find_best_match("firefux", candidates, limit=1)
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0][0], "firefox")


class TestConfigManager(unittest.TestCase):
    """Test configuration management."""

    def test_config_creation(self):
        """Test creating ConfigManager."""
        from aipp_opener.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            config = ConfigManager(config_file=temp_path)
            self.assertIsNotNone(config.get())
            self.assertEqual(config.get().ai.provider, "ollama")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_config_update(self):
        """Test updating configuration."""
        from aipp_opener.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            config = ConfigManager(config_file=temp_path)
            config.update(provider="gemini", model="gemini-pro")

            self.assertEqual(config.get().ai.provider, "gemini")
            self.assertEqual(config.get().ai.model, "gemini-pro")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_config_persistence(self):
        """Test configuration persistence."""
        from aipp_opener.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Create and save config
            config1 = ConfigManager(config_file=temp_path)
            config1.update(provider="openai")

            # Load config again
            config2 = ConfigManager(config_file=temp_path)
            self.assertEqual(config2.get().ai.provider, "openai")
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestExecutionResult(unittest.TestCase):
    """Test ExecutionResult dataclass."""

    def test_execution_result_success(self):
        """Test creating successful ExecutionResult."""
        from aipp_opener.executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            app_name="firefox",
            executable="/usr/bin/firefox",
            message="Launched successfully",
            pid=12345,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.pid, 12345)

    def test_execution_result_failure(self):
        """Test creating failed ExecutionResult."""
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
    """Test application executor."""

    def setUp(self):
        from aipp_opener.executor import AppExecutor

        self.executor = AppExecutor(use_notifications=False)

    def test_find_executable(self):
        """Test finding executable in PATH."""
        # Should find common executables
        path = self.executor._find_executable("python3")
        self.assertIsNotNone(path)

    def test_find_nonexistent_executable(self):
        """Test finding nonexistent executable."""
        path = self.executor._find_executable("nonexistent_app_xyz123")
        self.assertIsNone(path)

    def test_is_executable(self):
        """Test checking if executable exists."""
        self.assertTrue(self.executor.is_executable("python3"))
        self.assertFalse(self.executor.is_executable("nonexistent_app_xyz123"))


class TestHistoryManager(unittest.TestCase):
    """Test history management."""

    def setUp(self):
        import tempfile

        from aipp_opener.history import HistoryManager

        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.temp_dir.name) / "history.json"
        self.history = HistoryManager(history_file=self.history_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_launch(self):
        """Test recording app launch."""
        self.history.record("open firefox", "firefox", "/usr/bin/firefox")

        entries = self.history.get_recent(1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["app_name"], "firefox")

    def test_get_frequent_apps(self):
        """Test getting frequent apps."""
        # Record multiple launches
        for _ in range(5):
            self.history.record("open firefox", "firefox", "/usr/bin/firefox")
        for _ in range(3):
            self.history.record("open chrome", "chrome", "/usr/bin/chrome")

        frequent = self.history.get_frequent_apps(5)
        self.assertEqual(len(frequent), 2)
        self.assertEqual(frequent[0]["app_name"], "firefox")
        self.assertEqual(frequent[0]["count"], 5)

    def test_get_predictions(self):
        """Test getting predictions."""
        self.history.record("open firefox", "firefox", "/usr/bin/firefox")
        self.history.record("open firefox", "firefox", "/usr/bin/firefox")

        predictions = self.history.get_predictions("fire")
        self.assertIn("firefox", predictions)

    def test_get_stats(self):
        """Test getting statistics."""
        self.history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        self.history.record("open nonexistent", "nonexistent", "/nonexistent", success=False)

        stats = self.history.get_stats()
        self.assertEqual(stats["total_launches"], 2)
        self.assertEqual(stats["successful_launches"], 1)
        self.assertEqual(stats["failed_launches"], 1)


class TestAIProviders(unittest.TestCase):
    """Test AI provider classes."""

    def test_ollama_provider_creation(self):
        """Test creating Ollama provider."""
        from aipp_opener.ai.ollama import OllamaProvider

        provider = OllamaProvider(model="llama3.2")
        self.assertEqual(provider.name, "ollama")
        self.assertEqual(provider.model, "llama3.2")

    def test_ollama_provider_availability(self):
        """Test Ollama provider availability check."""
        from aipp_opener.ai.ollama import OllamaProvider

        provider = OllamaProvider()
        # May or may not be available depending on setup
        result = provider.is_available()
        self.assertIsInstance(result, bool)

    def test_gemini_provider_creation(self):
        """Test creating Gemini provider."""
        from aipp_opener.ai.gemini import GeminiProvider

        provider = GeminiProvider(api_key="test_key")
        self.assertEqual(provider.name, "gemini")

    def test_openai_provider_creation(self):
        """Test creating OpenAI provider."""
        from aipp_opener.ai.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="test_key")
        self.assertEqual(provider.name, "openai")

    def test_openrouter_provider_creation(self):
        """Test creating OpenRouter provider."""
        from aipp_opener.ai.openrouter import OpenRouterProvider

        provider = OpenRouterProvider(api_key="test_key")
        self.assertEqual(provider.name, "openrouter")


class TestIconFinder(unittest.TestCase):
    """Test icon finding functionality."""

    def test_icon_finder_creation(self):
        """Test creating IconFinder."""
        from aipp_opener.icons import IconFinder

        finder = IconFinder()
        self.assertIsNotNone(finder)

    def test_icon_info_creation(self):
        """Test creating IconInfo."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(name="firefox", path="/usr/share/icons/firefox.png")
        self.assertEqual(icon.name, "firefox")
        self.assertIsNotNone(icon.path)


class TestDetectorBase(unittest.TestCase):
    """Test detector base functionality."""

    def test_app_detector_abstract(self):
        """Test that AppDetector is abstract."""
        from aipp_opener.detectors.base import AppDetector

        with self.assertRaises(TypeError):
            AppDetector()


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_full_launch_simulation(self):
        """Test simulating a full app launch flow."""
        from aipp_opener.categories import AppCategorizer, AppCategory
        from aipp_opener.ai.nlp import NLPProcessor
        from aipp_opener.executor import AppExecutor

        # Simulate user input
        user_input = "open firefox"

        # Extract intent
        nlp = NLPProcessor()
        extracted = nlp.extract_app_intent(user_input)
        self.assertEqual(extracted, "firefox")

        # Categorize
        categorizer = AppCategorizer()
        category = categorizer.categorize(extracted)
        self.assertEqual(category, AppCategory.BROWSER)

        # Check if executable exists (may not in test environment)
        executor = AppExecutor(use_notifications=False)
        # Just verify the executor is created properly
        self.assertIsNotNone(executor)


if __name__ == "__main__":
    unittest.main()
