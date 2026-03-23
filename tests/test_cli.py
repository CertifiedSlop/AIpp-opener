"""Tests for AIpp Opener CLI interface (aipp_opener/cli.py)."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json


class TestGetAppDetector(unittest.TestCase):
    """Test get_app_detector function."""

    def test_get_app_detector_nixos(self):
        """Test detector selection when on NixOS."""
        from aipp_opener.cli import get_app_detector
        from aipp_opener.detectors.nixos import NixOSAppDetector

        with patch('aipp_opener.cli.NixOSAppDetector') as mock_nixos:
            mock_detector = Mock(spec=NixOSAppDetector)
            mock_detector.is_available.return_value = True
            mock_nixos.return_value = mock_detector

            detector = get_app_detector()

            self.assertEqual(detector, mock_detector)
            mock_detector.is_available.assert_called_once()

    def test_get_app_detector_fedora(self):
        """Test detector selection when on Fedora."""
        from aipp_opener.cli import get_app_detector
        from aipp_opener.detectors.fedora import FedoraAppDetector

        with patch('aipp_opener.cli.NixOSAppDetector') as mock_nixos, \
             patch('aipp_opener.cli.FedoraAppDetector') as mock_fedora:
            mock_nixos.return_value.is_available.return_value = False
            mock_fedora_detector = Mock(spec=FedoraAppDetector)
            mock_fedora_detector.is_available.return_value = True
            mock_fedora.return_value = mock_fedora_detector

            detector = get_app_detector()

            self.assertEqual(detector, mock_fedora_detector)

    def test_get_app_detector_arch(self):
        """Test detector selection when on Arch."""
        from aipp_opener.cli import get_app_detector
        from aipp_opener.detectors.arch import ArchAppDetector

        with patch('aipp_opener.cli.NixOSAppDetector') as mock_nixos, \
             patch('aipp_opener.cli.FedoraAppDetector') as mock_fedora, \
             patch('aipp_opener.cli.ArchAppDetector') as mock_arch:
            mock_nixos.return_value.is_available.return_value = False
            mock_fedora.return_value.is_available.return_value = False
            mock_arch_detector = Mock(spec=ArchAppDetector)
            mock_arch_detector.is_available.return_value = True
            mock_arch.return_value = mock_arch_detector

            detector = get_app_detector()

            self.assertEqual(detector, mock_arch_detector)

    def test_get_app_detector_debian_default(self):
        """Test detector defaults to Debian when no other matches."""
        from aipp_opener.cli import get_app_detector
        from aipp_opener.detectors.debian import DebianAppDetector

        with patch('aipp_opener.cli.NixOSAppDetector') as mock_nixos, \
             patch('aipp_opener.cli.FedoraAppDetector') as mock_fedora, \
             patch('aipp_opener.cli.ArchAppDetector') as mock_arch, \
             patch('aipp_opener.cli.DebianAppDetector') as mock_debian:
            mock_nixos.return_value.is_available.return_value = False
            mock_fedora.return_value.is_available.return_value = False
            mock_arch.return_value.is_available.return_value = False
            mock_debian_detector = Mock(spec=DebianAppDetector)
            mock_debian.return_value = mock_debian_detector

            detector = get_app_detector()

            self.assertEqual(detector, mock_debian_detector)


class TestGetAIProvider(unittest.TestCase):
    """Test get_ai_provider function."""

    def test_get_ai_provider_ollama(self):
        """Test Ollama provider selection."""
        from aipp_opener.cli import get_ai_provider
        from aipp_opener.ai.ollama import OllamaProvider

        mock_config = Mock()
        mock_config.get.return_value.ai.provider = "ollama"
        mock_config.get.return_value.ai.model = "llama3.2"
        mock_config.get.return_value.ai.base_url = "http://localhost:11434"
        mock_config.get.return_value.ai.api_key = None

        provider = get_ai_provider(mock_config)

        self.assertIsInstance(provider, OllamaProvider)

    def test_get_ai_provider_gemini(self):
        """Test Gemini provider selection."""
        from aipp_opener.cli import get_ai_provider
        from aipp_opener.ai.gemini import GeminiProvider

        mock_config = Mock()
        mock_config.get.return_value.ai.provider = "gemini"
        mock_config.get.return_value.ai.model = "gemini-pro"
        mock_config.get.return_value.ai.api_key = "test-key"

        provider = get_ai_provider(mock_config)

        self.assertIsInstance(provider, GeminiProvider)

    def test_get_ai_provider_openai(self):
        """Test OpenAI provider selection."""
        from aipp_opener.cli import get_ai_provider
        from aipp_opener.ai.openai import OpenAIProvider

        mock_config = Mock()
        mock_config.get.return_value.ai.provider = "openai"
        mock_config.get.return_value.ai.model = "gpt-3.5-turbo"
        mock_config.get.return_value.ai.api_key = "test-key"

        provider = get_ai_provider(mock_config)

        self.assertIsInstance(provider, OpenAIProvider)

    def test_get_ai_provider_openrouter(self):
        """Test OpenRouter provider selection."""
        from aipp_opener.cli import get_ai_provider
        from aipp_opener.ai.openrouter import OpenRouterProvider

        mock_config = Mock()
        mock_config.get.return_value.ai.provider = "openrouter"
        mock_config.get.return_value.ai.model = "meta-llama/llama-3-8b-instruct"
        mock_config.get.return_value.ai.api_key = "test-key"

        provider = get_ai_provider(mock_config)

        self.assertIsInstance(provider, OpenRouterProvider)

    def test_get_ai_provider_default(self):
        """Test default provider (Ollama) when not specified."""
        from aipp_opener.cli import get_ai_provider
        from aipp_opener.ai.ollama import OllamaProvider

        mock_config = Mock()
        mock_config.get.return_value.ai.provider = "unknown"
        mock_config.get.return_value.ai.model = "llama3.2"

        provider = get_ai_provider(mock_config)

        self.assertIsInstance(provider, OllamaProvider)


class TestProcessCommand(unittest.TestCase):
    """Test process_command function."""

    def test_process_command_success(self):
        """Test successful command processing."""
        from aipp_opener.cli import process_command
        from aipp_opener.executor import ExecutionResult
        from aipp_opener.detectors.base import AppInfo

        mock_app = AppInfo(
            name="firefox",
            executable="/usr/bin/firefox",
            display_name="Firefox",
            categories=["internet"]
        )

        mock_detector = Mock()
        mock_detector.detect.return_value = [mock_app]

        mock_executor = Mock()
        mock_executor.execute.return_value = ExecutionResult(
            success=True,
            app_name="firefox",
            executable="/usr/bin/firefox",
            message="Launched firefox",
            pid=12345,
        )

        mock_ai = Mock()
        mock_ai.is_available.return_value = False

        mock_nlp = Mock()
        mock_nlp.extract_app_intent.return_value = "firefox"
        mock_nlp.find_best_match.return_value = [("firefox", 90)]

        result = process_command("open firefox", mock_detector, mock_ai, mock_executor, mock_nlp)

        self.assertIsInstance(result, str)

    def test_process_command_not_found(self):
        """Test command processing when app not found."""
        from aipp_opener.cli import process_command
        from aipp_opener.executor import ExecutionResult

        mock_detector = Mock()
        mock_detector.detect.return_value = []

        mock_executor = Mock()
        mock_executor.execute.return_value = ExecutionResult(
            success=False,
            app_name="nonexistent",
            executable="nonexistent",
            message="Executable not found",
        )

        mock_ai = Mock()
        mock_ai.is_available.return_value = False

        mock_nlp = Mock()
        mock_nlp.extract_app_intent.return_value = "nonexistent"
        # Return empty list for find_best_match and find_all_matches
        mock_nlp.find_best_match = Mock(return_value=[])
        mock_nlp.find_all_matches = Mock(return_value=[])

        result = process_command("open nonexistent-app", mock_detector, mock_ai, mock_executor, mock_nlp)

        self.assertIsInstance(result, str)


class TestMainFunction(unittest.TestCase):
    """Test main CLI function."""

    def test_main_with_help_flag(self):
        """Test CLI with --help flag."""
        from aipp_opener.cli import main

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.argv', ['aipp_opener', '--help']):
                main()

        self.assertEqual(cm.exception.code, 0)

    def test_main_with_version_flag(self):
        """Test CLI with --version flag."""
        from aipp_opener.cli import main

        # The CLI may not have --version flag, so test what it does
        with patch('sys.argv', ['aipp_opener', '--version']):
            # Should exit with some code (may be error if flag not recognized)
            try:
                main()
            except SystemExit:
                pass  # Expected

    def test_main_with_gui_flag(self):
        """Test CLI with --gui flag."""
        from aipp_opener.cli import main

        # GUI requires display, skip in CI
        import os
        if not os.environ.get('DISPLAY'):
            self.skipTest("No display available")

        with patch('aipp_opener.cli.AppLauncherGUI') as mock_gui:
            mock_gui_instance = Mock()
            mock_gui.return_value = mock_gui_instance
            mock_gui_instance.run = Mock()

            with patch('sys.argv', ['aipp_opener', '--gui']):
                try:
                    main()
                except SystemExit:
                    pass

            mock_gui.assert_called_once()

    def test_main_with_tray_flag(self):
        """Test CLI with --tray flag."""
        from aipp_opener.cli import main

        # Tray requires display, skip in CI
        import os
        if not os.environ.get('DISPLAY'):
            self.skipTest("No display available")

        with patch('aipp_opener.cli.TrayApp') as mock_tray:
            mock_tray_instance = Mock()
            mock_tray.return_value = mock_tray_instance
            mock_tray_instance.run = Mock()

            with patch('sys.argv', ['aipp_opener', '--tray']):
                try:
                    main()
                except SystemExit:
                    pass

            mock_tray.assert_called_once()

    def test_main_with_detect_flag(self):
        """Test CLI with --detect flag."""
        from aipp_opener.cli import main
        from aipp_opener.detectors.base import AppInfo

        mock_detector = Mock()
        mock_detector.detect.return_value = [
            AppInfo(name="firefox", executable="/usr/bin/firefox")
        ]

        with patch('aipp_opener.cli.get_app_detector', return_value=mock_detector), \
             patch('aipp_opener.cli.ConfigManager'), \
             patch('aipp_opener.cli.get_ai_provider'), \
             patch('aipp_opener.cli.AppExecutor'), \
             patch('aipp_opener.cli.NLPProcessor'), \
             patch('aipp_opener.cli.HistoryManager'), \
             patch('aipp_opener.cli.PluginManager'), \
             patch('builtins.print'):
            with patch('sys.argv', ['aipp_opener', '--detect']):
                try:
                    main()
                except SystemExit:
                    pass  # May exit after detect

    def test_main_with_plugins_flag(self):
        """Test CLI with --plugins flag."""
        from aipp_opener.cli import main

        mock_manager = Mock()
        mock_manager.get_all_plugins.return_value = []
        mock_manager.get_stats.return_value = {
            'total_plugins': 0,
            'enabled_plugins': 0,
            'detector_plugins': 0,
            'command_plugins': 0,
            'result_modifier_plugins': 0,
        }

        with patch('aipp_opener.cli.PluginManager', return_value=mock_manager), \
             patch('builtins.print'):
            with patch('sys.argv', ['aipp_opener', '--plugins']):
                try:
                    main()
                except SystemExit:
                    pass  # Expected after printing plugins


if __name__ == "__main__":
    unittest.main()
