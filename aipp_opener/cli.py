"""CLI interface for AIpp Opener."""

import argparse
import sys
import json
import logging
from typing import Optional

from aipp_opener.config import ConfigManager
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.detectors.base import AppDetector
from aipp_opener.ai.ollama import OllamaProvider
from aipp_opener.ai.gemini import GeminiProvider
from aipp_opener.ai.openai import OpenAIProvider
from aipp_opener.ai.openrouter import OpenRouterProvider
from aipp_opener.ai.base import AIProvider
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.executor import AppExecutor
from aipp_opener.voice import VoiceInput
from aipp_opener.history import HistoryManager
from aipp_opener.logger_config import LoggerConfig, get_logger

logger = get_logger(__name__)


def get_app_detector() -> AppDetector:
    """Get the appropriate app detector for the current system."""
    logger.debug("Detecting platform for app detector")
    nixos_detector = NixOSAppDetector()
    if nixos_detector.is_available():
        logger.info("Platform detected: NixOS")
        return nixos_detector

    debian_detector = DebianAppDetector()
    if debian_detector.is_available():
        logger.info("Platform detected: Debian/Ubuntu")
        return debian_detector

    # Default to NixOS detector (will still scan common paths)
    logger.info("Platform not detected, using generic NixOS detector")
    return nixos_detector


def get_ai_provider(config: ConfigManager) -> AIProvider:
    """Get the configured AI provider."""
    ai_config = config.get().ai

    if ai_config.provider == "ollama":
        provider = OllamaProvider(
            model=ai_config.model,
            base_url=ai_config.base_url or "http://localhost:11434",
        )
    elif ai_config.provider == "gemini":
        provider = GeminiProvider(
            api_key=ai_config.api_key,
            model=ai_config.model,
        )
    elif ai_config.provider == "openai":
        provider = OpenAIProvider(
            api_key=ai_config.api_key,
            model=ai_config.model,
            base_url=ai_config.base_url,
        )
    elif ai_config.provider == "openrouter":
        provider = OpenRouterProvider(
            api_key=ai_config.api_key,
            model=ai_config.model,
        )
    else:
        # Default to Ollama
        provider = OllamaProvider(model=ai_config.model)

    return provider


def process_command(
    user_input: str,
    detector: AppDetector,
    ai_provider: AIProvider,
    executor: AppExecutor,
    nlp: NLPProcessor,
    history: Optional[HistoryManager] = None,
    max_suggestions: int = 5,
) -> str:
    """
    Process a user command and launch the appropriate application.

    Args:
        user_input: The user's natural language command.
        detector: App detector instance.
        ai_provider: AI provider instance.
        executor: App executor instance.
        nlp: NLP processor instance.
        history: Optional history manager.
        max_suggestions: Maximum number of suggestions.

    Returns:
        Result message.
    """
    # Get all installed apps
    installed_apps = detector.detect()
    app_names = [app.name for app in installed_apps]
    app_executables = {app.name: app.executable for app in installed_apps}

    # Extract intent using NLP
    extracted = nlp.extract_app_intent(user_input)

    # Try to find a direct match using fuzzy matching
    matches = nlp.find_best_match(extracted, app_names, limit=1)

    if matches and matches[0][1] >= 80:
        # High confidence match
        app_name = matches[0][0]
        executable = app_executables.get(app_name, app_name)

        result = executor.execute(executable)

        if history and result.success:
            history.record(user_input, app_name, executable)

        return result.message

    # Try AI-based extraction if no good match
    if ai_provider.is_available():
        try:
            ai_suggestion = ai_provider.extract_app_name(user_input)
            ai_matches = nlp.find_best_match(ai_suggestion, app_names, limit=1)

            if ai_matches and ai_matches[0][1] >= 60:
                app_name = ai_matches[0][0]
                executable = app_executables.get(app_name, app_name)

                result = executor.execute(executable)

                if history and result.success:
                    history.record(user_input, app_name, executable)

                return result.message
        except Exception:
            pass  # Fall back to suggestions

    # No good match - provide suggestions
    all_matches = nlp.find_all_matches(extracted, app_names, min_score=50)
    suggestions = [m[0] for m in all_matches[:max_suggestions]]

    if suggestions:
        suggestion_list = ", ".join(suggestions)
        return f"No exact match found. Did you mean: {suggestion_list}?"
    else:
        return f"Could not find any matching applications for '{extracted}'"


def interactive_mode(
    detector: AppDetector,
    ai_provider: AIProvider,
    executor: AppExecutor,
    nlp: NLPProcessor,
    history: Optional[HistoryManager],
    config: ConfigManager,
) -> None:
    """Run in interactive mode."""
    print("AIpp Opener - Type 'quit' or 'exit' to stop")
    print("Type 'help' for available commands")
    print()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if user_input.lower() == "help":
            print_help()
            continue

        if user_input.lower() == "stats" and history:
            stats = history.get_stats()
            print(json.dumps(stats, indent=2))
            continue

        if user_input.lower() == "frequent" and history:
            frequent = history.get_frequent_apps(10)
            for i, app in enumerate(frequent, 1):
                print(f"{i}. {app['app_name']} ({app['count']} times)")
            continue

        result = process_command(
            user_input,
            detector,
            ai_provider,
            executor,
            nlp,
            history,
            config.get().max_suggestions,
        )
        print(result)
        print()


def print_help() -> None:
    """Print help information."""
    print("""
Available commands:
  open <app>     - Open an application
  launch <app>   - Launch an application
  start <app>    - Start an application
  run <app>      - Run an application

  help           - Show this help
  stats          - Show usage statistics
  frequent       - Show frequently used apps
  quit/exit      - Exit interactive mode

Examples:
  > open firefox
  > launch vs code
  > start terminal
  > run spotify
""")


def voice_mode(
    detector: AppDetector,
    ai_provider: AIProvider,
    executor: AppExecutor,
    nlp: NLPProcessor,
    history: Optional[HistoryManager],
    config: ConfigManager,
) -> None:
    """Run in voice input mode."""
    voice = VoiceInput()

    if not voice.is_available():
        print("Voice input is not available. Make sure SpeechRecognition is installed.")
        print("Install with: pip install SpeechRecognition")
        return

    print("Voice mode activated. Speak your command.")
    print("Say 'quit' or 'exit' to stop.")
    print()

    while True:
        try:
            text = voice.listen_once()

            if not text:
                continue

            if text.lower() in ("quit", "exit", "stop"):
                print("Goodbye!")
                break

            print(f"You said: {text}")

            result = process_command(
                text,
                detector,
                ai_provider,
                executor,
                nlp,
                history,
                config.get().max_suggestions,
            )
            print(result)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AIpp Opener - AI-powered application launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "open firefox"     - Open Firefox
  %(prog)s "launch vs code"   - Launch VS Code
  %(prog)s --voice            - Voice input mode
  %(prog)s --interactive      - Interactive mode
  %(prog)s --gui              - Open GUI interface
  %(prog)s --suggest browser  - Get suggestions for 'browser'
        """
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="Natural language command (e.g., 'open firefox')"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "-v", "--voice",
        action="store_true",
        help="Enable voice input mode"
    )
    parser.add_argument(
        "-s", "--suggest",
        metavar="QUERY",
        help="Get app suggestions for a query"
    )
    parser.add_argument(
        "--list-apps",
        action="store_true",
        help="List detected applications"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show/edit configuration"
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "gemini", "openai", "openrouter"],
        help="Override AI provider"
    )
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="Disable system notifications"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Disable usage history"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open GUI interface"
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Run in system tray mode"
    )
    parser.add_argument(
        "--shortcut",
        action="store_true",
        help="Enable global keyboard shortcut (Ctrl+Alt+Space)"
    )
    parser.add_argument(
        "--shortcut-key",
        type=str,
        default="<ctrl><alt>space",
        help="Custom keyboard shortcut (default: <ctrl><alt>space)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run first-time setup wizard"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set logging level"
    )

    args = parser.parse_args()

    # Load configuration
    config = ConfigManager()

    # Initialize logging
    log_level_str = args.log_level or config.get().ai.log_level or "INFO"
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    LoggerConfig.setup(log_level=log_level)
    logger.info("AIpp Opener starting (log level: %s)", log_level_str)

    # Override provider if specified
    if args.provider:
        logger.info("Overriding AI provider: %s", args.provider)
        config.update(provider=args.provider)

    # Initialize components
    detector = get_app_detector()
    ai_provider = get_ai_provider(config)
    executor = AppExecutor(use_notifications=not args.no_notifications)
    nlp = NLPProcessor()
    history = HistoryManager() if not args.no_history and config.get().history_enabled else None

    # Handle --setup
    if args.setup:
        from aipp_opener.setup_wizard import main as setup_main
        setup_main()
        return

    # Handle --config
    if args.config:
        print("Current configuration:")
        print(json.dumps(config.get().model_dump(), indent=2))
        return

    # Handle --list-apps
    if args.list_apps:
        apps = detector.detect()
        print(f"Detected {len(apps)} applications:")
        for app in apps[:50]:  # Limit output
            print(f"  - {app.name}: {app.executable}")
        if len(apps) > 50:
            print(f"  ... and {len(apps) - 50} more")
        return

    # Handle --suggest
    if args.suggest:
        apps = detector.detect()
        app_names = [app.name for app in apps]

        if ai_provider.is_available():
            try:
                suggestions = ai_provider.suggest_apps(
                    args.suggest,
                    app_names,
                    config.get().max_suggestions
                )
                print(f"Suggestions for '{args.suggest}':")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                return
            except Exception:
                pass

        # Fallback to NLP matching
        matches = nlp.find_all_matches(args.suggest, app_names, min_score=40)
        print(f"Suggestions for '{args.suggest}':")
        for i, (name, score) in enumerate(matches[:config.get().max_suggestions], 1):
            print(f"  {i}. {name} (score: {score})")
        return

    # Handle --gui
    if args.gui:
        from aipp_opener.gui import main as gui_main
        gui_main()
        return

    # Handle --tray
    if args.tray:
        from aipp_opener.tray import main as tray_main
        tray_main()
        return

    # Handle --shortcut
    if args.shortcut:
        from aipp_opener.keyboard import QuickLauncher
        launcher = QuickLauncher(shortcut=args.shortcut_key)
        launcher.start()
        print(f"Keyboard shortcut enabled: {args.shortcut_key}")
        print("Press the shortcut to open quick launcher. Press Ctrl+C to exit.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop()
            print("\nExiting...")
        return

    # Handle --voice
    if args.voice:
        voice_mode(detector, ai_provider, executor, nlp, history, config)
        return

    # Handle --interactive or no command
    if args.interactive or not args.command:
        interactive_mode(detector, ai_provider, executor, nlp, history, config)
        return

    # Handle single command
    result = process_command(
        args.command,
        detector,
        ai_provider,
        executor,
        nlp,
        history,
        config.get().max_suggestions,
    )
    print(result)


if __name__ == "__main__":
    main()
