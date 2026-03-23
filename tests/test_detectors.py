"""Tests for AIpp Opener detectors and additional modules."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestNixOSDetector(unittest.TestCase):
    """Test NixOS app detector (aipp_opener/detectors/nixos.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.nixos import NixOSAppDetector

        self.detector = NixOSAppDetector()

    def test_is_available(self):
        """Test detector availability check."""
        # Just test it returns a boolean
        result = self.detector.is_available()
        self.assertIsInstance(result, bool)

    def test_detect_returns_list(self):
        """Test that detect returns a list."""
        apps = self.detector.detect()
        self.assertIsInstance(apps, list)


class TestDebianDetector(unittest.TestCase):
    """Test Debian app detector (aipp_opener/detectors/debian.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.debian import DebianAppDetector

        self.detector = DebianAppDetector()

    def test_is_available(self):
        """Test detector availability check."""
        result = self.detector.is_available()
        self.assertIsInstance(result, bool)

    def test_detect_returns_list(self):
        """Test that detect returns a list."""
        apps = self.detector.detect()
        self.assertIsInstance(apps, list)


class TestFedoraDetector(unittest.TestCase):
    """Test Fedora app detector (aipp_opener/detectors/fedora.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.fedora import FedoraAppDetector

        self.detector = FedoraAppDetector()

    def test_is_available(self):
        """Test detector availability check."""
        result = self.detector.is_available()
        self.assertIsInstance(result, bool)

    @unittest.skipUnless(
        Path("/etc/fedora-release").exists(),
        "Test only runs on Fedora systems"
    )
    def test_detect_returns_list(self):
        """Test that detect returns a list."""
        apps = self.detector.detect()
        self.assertIsInstance(apps, list)


class TestArchDetector(unittest.TestCase):
    """Test Arch Linux app detector (aipp_opener/detectors/arch.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.arch import ArchAppDetector

        self.detector = ArchAppDetector()

    def test_is_available(self):
        """Test detector availability check."""
        result = self.detector.is_available()
        self.assertIsInstance(result, bool)

    @unittest.skipUnless(
        Path("/etc/arch-release").exists(),
        "Test only runs on Arch systems"
    )
    def test_detect_returns_list(self):
        """Test that detect returns a list."""
        apps = self.detector.detect()
        self.assertIsInstance(apps, list)


class TestExecutor(unittest.TestCase):
    """Test application executor (aipp_opener/executor.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.executor import AppExecutor

        self.executor = AppExecutor(use_notifications=False)

    def test_execute_returns_result(self):
        """Test that execute returns ExecutionResult."""
        from aipp_opener.executor import ExecutionResult

        result = self.executor.execute("true")  # 'true' command returns 0
        self.assertIsInstance(result, ExecutionResult)


class TestCategories(unittest.TestCase):
    """Test app categorization (aipp_opener/categories.py)."""

    def test_app_category_enum(self):
        """Test category enum values."""
        from aipp_opener.categories import AppCategory

        self.assertEqual(AppCategory.BROWSER.value, "browser")
        self.assertEqual(AppCategory.EDITOR.value, "editor")
        self.assertEqual(AppCategory.IDE.value, "ide")
        self.assertEqual(AppCategory.MEDIA.value, "media")

    def test_app_categorizer(self):
        """Test AppCategorizer."""
        from aipp_opener.categories import AppCategorizer

        categorizer = AppCategorizer()
        category = categorizer.categorize("firefox")
        self.assertIsNotNone(category)


class TestIcons(unittest.TestCase):
    """Test icon detection (aipp_opener/icons.py)."""

    def test_icon_info_dataclass(self):
        """Test IconInfo dataclass."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(name="test", path="/test/path")
        self.assertEqual(icon.name, "test")
        self.assertEqual(icon.path, "/test/path")


class TestAIProviders(unittest.TestCase):
    """Test AI provider modules."""

    def test_ollama_provider(self):
        """Test Ollama provider initialization."""
        from aipp_opener.ai.ollama import OllamaProvider
        from aipp_opener.config import AppConfig

        config = AppConfig()
        provider = OllamaProvider(config)

        self.assertIsNotNone(provider)
        self.assertFalse(provider.is_available())  # No Ollama running in test

    def test_nlp_processor(self):
        """Test NLP processor."""
        from aipp_opener.ai.nlp import NLPProcessor

        nlp = NLPProcessor()

        # Test app intent extraction
        intent = nlp.extract_app_intent("open firefox")
        self.assertIsNotNone(intent)

        # Test finding matches
        app_names = ["firefox", "chrome"]
        matches = nlp.find_all_matches("firefux", app_names, min_score=40)
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0][0], "firefox")

        # Test action extraction (if available)
        if hasattr(nlp, 'extract_action'):
            action = nlp.extract_action("launch")
            self.assertIsNotNone(action)


class TestHistory(unittest.TestCase):
    """Test usage history (aipp_opener/history.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.history import HistoryManager

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.history = HistoryManager(history_file=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_record_usage(self):
        """Test recording app usage."""
        self.history.record("firefox", "firefox", "/usr/bin/firefox")

        frequent = self.history.get_frequent_apps(5)
        self.assertGreater(len(frequent), 0)

    def test_get_frequent_apps(self):
        """Test getting frequent apps."""
        self.history.record("test-app", "test", "/usr/bin/test")
        self.history.record("test-app", "test", "/usr/bin/test")

        frequent = self.history.get_frequent_apps(5)
        app_names = [app['app_name'] for app in frequent]
        self.assertIn("test", app_names)

    def test_clear_history(self):
        """Test clearing history."""
        self.history.record("test", "test", "/usr/bin/test")
        self.history.clear()

        frequent = self.history.get_frequent_apps(5)
        self.assertEqual(len(frequent), 0)

    def test_history_persistence(self):
        """Test history persists across instances."""
        self.history.record("persistent", "persistent", "/usr/bin/persistent")

        # Create new instance with same file
        from aipp_opener.history import HistoryManager
        new_history = HistoryManager(history_file=Path(self.temp_file.name))
        frequent = new_history.get_frequent_apps(5)
        app_names = [app['app_name'] for app in frequent]
        self.assertIn("persistent", app_names)


class TestConfig(unittest.TestCase):
    """Test configuration management (aipp_opener/config.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.config import ConfigManager

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.config = ConfigManager(config_file=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_get_config(self):
        """Test getting configuration."""
        config = self.config.get()
        self.assertIsNotNone(config)

    def test_update_config(self):
        """Test updating configuration."""
        self.config.update(max_suggestions=10)
        config = self.config.get()
        self.assertEqual(config.max_suggestions, 10)


class TestAIProviders(unittest.TestCase):
    """Test AI provider modules."""

    def test_ollama_provider(self):
        """Test Ollama provider initialization."""
        from aipp_opener.ai.ollama import OllamaProvider
        from aipp_opener.config import AppConfig

        config = AppConfig()
        provider = OllamaProvider(config)
        
        self.assertIsNotNone(provider)
        self.assertFalse(provider.is_available())  # No Ollama running in test

    def test_find_matches(self):
        """Test fuzzy matching."""
        from aipp_opener.ai.nlp import NLPProcessor

        nlp = NLPProcessor()
        app_names = ["firefox", "chrome", "code"]
        
        matches = nlp.find_all_matches("firefux", app_names, min_score=40)
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0][0], "firefox")


if __name__ == "__main__":
    unittest.main()
