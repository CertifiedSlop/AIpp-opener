"""Tests for setup wizard module."""

import unittest
from unittest.mock import patch, MagicMock
import io
import sys


class TestSetupWizard(unittest.TestCase):
    """Tests for SetupWizard class."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                self.wizard = SetupWizard()

    def test_wizard_init(self):
        """Test SetupWizard initialization."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()
                self.assertIsNotNone(wizard)
                self.assertIsNotNone(wizard.config)
                self.assertIsNotNone(wizard.nlp)

    def test_welcome_method_exists(self):
        """Test that _welcome method exists."""
        self.assertTrue(hasattr(self.wizard, '_welcome'))

    def test_configure_ai_provider_method_exists(self):
        """Test that _configure_ai_provider method exists."""
        self.assertTrue(hasattr(self.wizard, '_configure_ai_provider'))

    def test_test_ai_provider_method_exists(self):
        """Test that _test_ai_provider method exists."""
        self.assertTrue(hasattr(self.wizard, '_test_ai_provider'))

    def test_configure_features_method_exists(self):
        """Test that _configure_features method exists."""
        self.assertTrue(hasattr(self.wizard, '_configure_features'))

    def test_test_app_detection_method_exists(self):
        """Test that _test_app_detection method exists."""
        self.assertTrue(hasattr(self.wizard, '_test_app_detection'))

    def test_summary_method_exists(self):
        """Test that _summary method exists."""
        self.assertTrue(hasattr(self.wizard, '_summary'))

    def test_get_input_method_exists(self):
        """Test that _get_input method exists."""
        self.assertTrue(hasattr(self.wizard, '_get_input'))

    def test_setup_ollama_method_exists(self):
        """Test that _setup_ollama method exists."""
        self.assertTrue(hasattr(self.wizard, '_setup_ollama'))

    def test_setup_gemini_method_exists(self):
        """Test that _setup_gemini method exists."""
        self.assertTrue(hasattr(self.wizard, '_setup_gemini'))

    def test_setup_openai_method_exists(self):
        """Test that _setup_openai method exists."""
        self.assertTrue(hasattr(self.wizard, '_setup_openai'))

    def test_setup_openrouter_method_exists(self):
        """Test that _setup_openrouter method exists."""
        self.assertTrue(hasattr(self.wizard, '_setup_openrouter'))


class TestSetupWizardGetInput(unittest.TestCase):
    """Tests for SetupWizard._get_input method."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                self.wizard = SetupWizard()

    @patch('builtins.input', return_value='')
    def test_get_input_default(self, mock_input):
        """Test _get_input with default value."""
        result = self.wizard._get_input("Test prompt", default="default_value")
        self.assertEqual(result, "default_value")

    @patch('builtins.input', return_value='custom')
    def test_get_input_custom(self, mock_input):
        """Test _get_input with custom value."""
        result = self.wizard._get_input("Test prompt", default="default")
        self.assertEqual(result, "custom")

    @patch('builtins.input', return_value='  ')
    def test_get_input_whitespace(self, mock_input):
        """Test _get_input with whitespace input."""
        result = self.wizard._get_input("Test", default="default")
        self.assertEqual(result, "default")


class TestSetupWizardSetupMethods(unittest.TestCase):
    """Tests for SetupWizard setup methods."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                self.wizard = SetupWizard()

    def test_setup_ollama_exists(self):
        """Test _setup_ollama method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_setup_ollama', None)))

    def test_setup_gemini_exists(self):
        """Test _setup_gemini method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_setup_gemini', None)))

    def test_setup_openai_exists(self):
        """Test _setup_openai method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_setup_openai', None)))

    def test_setup_openrouter_exists(self):
        """Test _setup_openrouter method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_setup_openrouter', None)))


class TestSetupWizardRun(unittest.TestCase):
    """Tests for SetupWizard.run method."""

    def test_run_with_keyboard_interrupt(self):
        """Test run method handles keyboard interrupt."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()

                with patch.object(wizard, '_welcome', side_effect=KeyboardInterrupt()):
                    with patch('builtins.print'):
                        with self.assertRaises(SystemExit):
                            wizard.run()

    def test_run_calls_all_steps(self):
        """Test run method calls all setup steps."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()

                with patch.object(wizard, '_welcome') as mock_welcome:
                    with patch.object(wizard, '_configure_ai_provider') as mock_ai:
                        with patch.object(wizard, '_test_ai_provider') as mock_test_ai:
                            with patch.object(wizard, '_configure_features') as mock_features:
                                with patch.object(wizard, '_test_app_detection') as mock_test_app:
                                    with patch.object(wizard, '_summary') as mock_summary:
                                        with patch('builtins.print'):
                                            with patch('builtins.input', return_value=''):
                                                wizard.run()

                mock_welcome.assert_called_once()
                mock_ai.assert_called_once()
                mock_test_ai.assert_called_once()
                mock_features.assert_called_once()
                mock_test_app.assert_called_once()
                mock_summary.assert_called_once()


class TestSetupWizardOutput(unittest.TestCase):
    """Tests for SetupWizard output methods."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.setup_wizard import SetupWizard

        with patch('aipp_opener.setup_wizard.ConfigManager'):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                self.wizard = SetupWizard()

    def test_welcome_method_exists(self):
        """Test _welcome method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_welcome', None)))

    def test_summary_method_exists(self):
        """Test _summary method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_summary', None)))

    def test_configure_ai_provider_exists(self):
        """Test _configure_ai_provider method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_configure_ai_provider', None)))

    def test_configure_features_exists(self):
        """Test _configure_features method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_configure_features', None)))

    def test_test_ai_provider_exists(self):
        """Test _test_ai_provider method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_test_ai_provider', None)))

    def test_test_app_detection_exists(self):
        """Test _test_app_detection method exists and is callable."""
        self.assertTrue(callable(getattr(self.wizard, '_test_app_detection', None)))


class TestSetupWizardConfigUpdates(unittest.TestCase):
    """Tests for SetupWizard config update functionality."""

    def test_wizard_updates_config(self):
        """Test that wizard can update config."""
        from aipp_opener.setup_wizard import SetupWizard

        mock_config = MagicMock()
        mock_config.get.return_value.notifications_enabled = True
        mock_config.get.return_value.history_enabled = True

        with patch('aipp_opener.setup_wizard.ConfigManager', return_value=mock_config):
            with patch('aipp_opener.setup_wizard.NLPProcessor'):
                wizard = SetupWizard()

                # Config should be accessible
                self.assertEqual(wizard.config, mock_config)


if __name__ == "__main__":
    unittest.main()
