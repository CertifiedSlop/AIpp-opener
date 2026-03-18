"""Setup wizard for first-time users."""

import sys
import json
from pathlib import Path
from typing import Optional

from aipp_opener.logger_config import get_logger, LoggerConfig
from aipp_opener.config import ConfigManager
from aipp_opener.ai.ollama import OllamaProvider
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.detectors.debian import DebianAppDetector

logger = get_logger(__name__)


class SetupWizard:
    """Interactive setup wizard for first-time users."""

    def __init__(self):
        """Initialize the setup wizard."""
        self.config = ConfigManager()
        self.nlp = NLPProcessor()
        logger.info("SetupWizard initialized")

    def run(self) -> None:
        """Run the setup wizard."""
        print("\n" + "=" * 60)
        print("  AIpp Opener - Setup Wizard")
        print("=" * 60)
        print("\nWelcome! This wizard will help you configure AIpp Opener.")
        print("Press Enter to accept defaults shown in [brackets].\n")

        try:
            self._welcome()
            self._configure_ai_provider()
            self._test_ai_provider()
            self._configure_features()
            self._test_app_detection()
            self._summary()
        except KeyboardInterrupt:
            print("\n\nSetup cancelled. You can run this wizard again with: aipp-opener --setup")
            logger.info("Setup wizard cancelled by user")
            sys.exit(1)

        print("\n✓ Setup complete! You can now use AIpp Opener.")
        print("  Run 'aipp-opener --help' for usage information.\n")
        logger.info("Setup wizard completed successfully")

    def _welcome(self) -> None:
        """Show welcome message."""
        # Already shown in run()
        pass

    def _configure_ai_provider(self) -> None:
        """Configure AI provider."""
        print("-" * 60)
        print("AI Provider Configuration")
        print("-" * 60)
        print("\nAIpp Opener uses AI to understand natural language commands.")
        print("Choose your AI provider:\n")
        print("  1. Ollama (Recommended - Free, Local, Private)")
        print("  2. Google Gemini (Cloud, API key required)")
        print("  3. OpenAI GPT (Cloud, API key required)")
        print("  4. OpenRouter (Cloud, Multiple models, API key required)")
        print("  5. Skip (Configure later)\n")

        choice = self._get_input("Select provider", default="1")

        if choice == "1":
            self._setup_ollama()
        elif choice == "2":
            self._setup_gemini()
        elif choice == "3":
            self._setup_openai()
        elif choice == "4":
            self._setup_openrouter()
        else:
            print("\nSkipping AI provider configuration.")
            logger.info("AI provider configuration skipped")

    def _setup_ollama(self) -> None:
        """Setup Ollama provider."""
        print("\nOllama is a local AI provider that runs on your machine.")
        print("It's free, private, and doesn't require an API key.\n")

        # Check if Ollama is installed
        provider = OllamaProvider()
        if provider.is_available():
            print("✓ Ollama is installed and running!")
            models = provider.list_models()
            if models:
                print(f"  Available models: {', '.join(models[:5])}")
                if len(models) > 5:
                    print(f"  ... and {len(models) - 5} more")
            else:
                print("  No models found. You'll need to pull a model.")
                print("  Run: ollama pull llama3.2")
        else:
            print("✗ Ollama is not installed or not running.")
            print("\nTo install Ollama:")
            print("  curl -fsSL https://ollama.ai/install.sh | sh")
            print("\nAfter installation, pull a model:")
            print("  ollama pull llama3.2")

        # Get model name
        model = self._get_input("Model name", default="llama3.2")
        base_url = self._get_input("Base URL", default="http://localhost:11434")

        self.config.update(provider="ollama", model=model, base_url=base_url)
        logger.info("Configured Ollama provider (model=%s, url=%s)", model, base_url)

    def _setup_gemini(self) -> None:
        """Setup Google Gemini provider."""
        print("\nGoogle Gemini requires an API key from Google AI Studio.")
        print("Get your free API key at: https://makersuite.google.com/app/apikey\n")

        api_key = self._get_input("Gemini API key", password=True)
        model = self._get_input("Model name", default="gemini-pro")

        self.config.update(provider="gemini", model=model, api_key=api_key)
        logger.info("Configured Gemini provider (model=%s)", model)

    def _setup_openai(self) -> None:
        """Setup OpenAI provider."""
        print("\nOpenAI GPT requires an API key from OpenAI.")
        print("Get your API key at: https://platform.openai.com/api-keys\n")

        api_key = self._get_input("OpenAI API key", password=True)
        model = self._get_input("Model name", default="gpt-3.5-turbo")
        base_url = self._get_input("Base URL (optional)", default="")

        self.config.update(provider="openai", model=model, api_key=api_key)
        if base_url:
            self.config.update(base_url=base_url)
        logger.info("Configured OpenAI provider (model=%s)", model)

    def _setup_openrouter(self) -> None:
        """Setup OpenRouter provider."""
        print("\nOpenRouter provides access to multiple AI models.")
        print("Get your API key at: https://openrouter.ai/keys\n")

        api_key = self._get_input("OpenRouter API key", password=True)
        model = self._get_input(
            "Model name",
            default="meta-llama/llama-3-8b-instruct"
        )

        self.config.update(provider="openrouter", model=model, api_key=api_key)
        logger.info("Configured OpenRouter provider (model=%s)", model)

    def _test_ai_provider(self) -> None:
        """Test the configured AI provider."""
        print("\n" + "-" * 60)
        print("Testing AI Provider")
        print("-" * 60)

        ai_config = self.config.get().ai
        if ai_config.provider == "ollama":
            provider = OllamaProvider(
                model=ai_config.model,
                base_url=ai_config.base_url or "http://localhost:11434",
            )
        else:
            # For other providers, just check if API key is set
            if ai_config.api_key:
                print(f"✓ {ai_config.provider.title()} configured with API key")
                logger.info("AI provider %s configured", ai_config.provider)
                return
            else:
                print("✗ No API key configured for " + ai_config.provider)
                return

        if provider.is_available():
            print(f"✓ {ai_config.provider.title()} is available!")
            print(f"  Model: {ai_config.model}")
            logger.info("AI provider %s is available", ai_config.provider)
        else:
            print(f"✗ {ai_config.provider.title()} is not available.")
            print("  Make sure the service is running and accessible.")
            logger.warning("AI provider %s is not available", ai_config.provider)

    def _configure_features(self) -> None:
        """Configure optional features."""
        print("\n" + "-" * 60)
        print("Feature Configuration")
        print("-" * 60)

        # Notifications
        current = self.config.get().notifications_enabled
        default = "y" if current else "n"
        choice = self._get_input(
            "Enable system notifications",
            default=default
        )
        self.config.update(notifications_enabled=choice.lower() == "y")

        # History
        current = self.config.get().history_enabled
        default = "y" if current else "n"
        choice = self._get_input(
            "Enable usage history (for predictions)",
            default=default
        )
        self.config.update(history_enabled=choice.lower() == "y")

        # Voice
        current = self.config.get().voice_enabled
        default = "y" if current else "n"
        choice = self._get_input(
            "Enable voice input (requires microphone)",
            default=default
        )
        self.config.update(voice_enabled=choice.lower() == "y")

        # Log level
        print("\nLogging level:")
        print("  1. DEBUG (Detailed debugging)")
        print("  2. INFO (General information)")
        print("  3. WARNING (Warnings only)")
        print("  4. ERROR (Errors only)")

        choice = self._get_input("Log level", default="2")
        log_levels = {"1": "DEBUG", "2": "INFO", "3": "WARNING", "4": "ERROR"}
        log_level = log_levels.get(choice, "INFO")
        self.config.update(log_level=log_level)

        logger.info(
            "Features configured: notifications=%s, history=%s, voice=%s, log_level=%s",
            self.config.get().notifications_enabled,
            self.config.get().history_enabled,
            self.config.get().voice_enabled,
            log_level
        )

    def _test_app_detection(self) -> None:
        """Test application detection."""
        print("\n" + "-" * 60)
        print("Testing Application Detection")
        print("-" * 60)

        print("\nDetecting installed applications...")

        nixos_detector = NixOSAppDetector()
        if nixos_detector.is_available():
            detector = nixos_detector
            print("Platform: NixOS")
        else:
            debian_detector = DebianAppDetector()
            if debian_detector.is_available():
                detector = debian_detector
                print("Platform: Debian/Ubuntu")
            else:
                detector = nixos_detector
                print("Platform: Generic")

        apps = detector.detect()
        print(f"\n✓ Detected {len(apps)} applications")

        if apps:
            print("\nSample applications:")
            for app in apps[:10]:
                print(f"  - {app.display_name or app.name}")
            if len(apps) > 10:
                print(f"  ... and {len(apps) - 10} more")

        logger.info("Detected %d applications", len(apps))

    def _summary(self) -> None:
        """Show setup summary."""
        print("\n" + "-" * 60)
        print("Setup Summary")
        print("-" * 60)

        ai_config = self.config.get().ai
        print(f"\nAI Provider: {ai_config.provider}")
        print(f"  Model: {ai_config.model}")
        if ai_config.base_url:
            print(f"  URL: {ai_config.base_url}")

        print(f"\nFeatures:")
        print(f"  Notifications: {'Enabled' if self.config.get().notifications_enabled else 'Disabled'}")
        print(f"  History: {'Enabled' if self.config.get().history_enabled else 'Disabled'}")
        print(f"  Voice: {'Enabled' if self.config.get().voice_enabled else 'Disabled'}")
        print(f"  Log Level: {ai_config.log_level}")

        print(f"\nConfiguration saved to:")
        print(f"  {self.config.config_file}")

    def _get_input(
        self,
        prompt: str,
        default: str = "",
        password: bool = False
    ) -> str:
        """Get user input with optional default."""
        if default:
            prompt = f"{prompt} [{default}]"
        prompt = f"{prompt}: "

        try:
            if password:
                import getpass
                value = getpass.getpass(prompt)
            else:
                value = input(prompt)

            return value.strip() or default
        except EOFError:
            return default


def main():
    """Main entry point for setup wizard."""
    LoggerConfig.setup(console_output=True, file_output=True)
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
