"""CLI interface for AIpp Opener."""

import argparse
import json
import logging
import sys
from typing import Optional

from aipp_opener.ai.base import AIProvider
from aipp_opener.ai.gemini import GeminiProvider
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.ai.ollama import OllamaProvider
from aipp_opener.ai.openai import OpenAIProvider
from aipp_opener.ai.openrouter import OpenRouterProvider
from aipp_opener.detectors.base import AppDetector
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.executor import AppExecutor
from aipp_opener.history import HistoryManager
from aipp_opener.logger_config import LoggerConfig, get_logger
from aipp_opener.config import ConfigManager
from aipp_opener.voice import VoiceInput
from aipp_opener.web_search import WebSearcher
from aipp_opener.aliases import AliasManager
from aipp_opener.groups import GroupManager

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
    # Initialize alias and group managers
    alias_manager = AliasManager()
    group_manager = GroupManager()

    # Check if input is an alias
    alias_command = alias_manager.get_command(user_input.strip())
    if alias_command:
        result = executor.execute(alias_command)
        if history and result.success:
            history.record(user_input, user_input, alias_command)
        return result.message

    # Check if input is a group name
    group = group_manager.get_group(user_input.strip())
    if group:
        success, results = group_manager.launch_group(user_input.strip(), executor)
        messages = []
        for result in results:
            status = "✓" if result.success else "✗"
            messages.append(f"{status} {result.app_name}: {result.message}")
        return "\n".join(messages)

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
        return f"No exact match found. Did you mean: {suggestion_list}?\nUse --web-search '{extracted}' to search online."
    else:
        return f"Could not find any matching applications for '{extracted}'.\nUse --web-search '{extracted}' to search online."


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

        # Handle alias commands in interactive mode
        if user_input.lower().startswith("alias "):
            alias_manager = AliasManager()
            parts = user_input[6:].strip()
            if "=" in parts:
                name, command = parts.split("=", 1)
                if alias_manager.add_alias(name.strip(), command.strip()):
                    print(f"Added alias: {name.strip()} -> {command.strip()}")
                else:
                    print(f"Alias '{name.strip()}' already exists")
            else:
                print("Usage: alias <name>=<command>")
            continue

        if user_input.lower() == "aliases":
            alias_manager = AliasManager()
            aliases = alias_manager.list_aliases()
            print(f"Custom aliases ({len(aliases)} total):")
            for alias in aliases:
                tags = f" [{', '.join(alias.tags)}]" if alias.tags else ""
                desc = f" - {alias.description}" if alias.description else ""
                print(f"  {alias.name} -> {alias.command}{tags}{desc}")
            continue

        if user_input.lower().startswith("unalias "):
            alias_manager = AliasManager()
            name = user_input[8:].strip()
            if alias_manager.remove_alias(name):
                print(f"Removed alias: {name}")
            else:
                print(f"Could not remove alias '{name}'")
            continue

        # Handle group commands in interactive mode
        if user_input.lower().startswith("group "):
            group_manager = GroupManager()
            group_name = user_input[6:].strip()
            print(f"Launching group: {group_name}")
            success, results = group_manager.launch_group(group_name, executor)
            for result in results:
                status = "✓" if result.success else "✗"
                print(f"  {status} {result.app_name}: {result.message}")
            continue

        if user_input.lower() == "groups":
            group_manager = GroupManager()
            groups = group_manager.list_groups()
            print(f"App groups ({len(groups)} total):")
            for group in groups:
                apps = ", ".join(group.apps)
                desc = f" - {group.description}" if group.description else ""
                print(f"  {group.name}: {apps}{desc}")
            continue

        if user_input.lower().startswith("create-group "):
            group_manager = GroupManager()
            parts = user_input[13:].strip()
            if "=" in parts:
                name, apps_str = parts.split("=", 1)
                apps = [app.strip() for app in apps_str.split(",")]
                if group_manager.add_group(name.strip(), apps):
                    print(f"Created group: {name.strip()} ({len(apps)} apps)")
                else:
                    print(f"Group '{name.strip()}' already exists")
            else:
                print("Usage: create-group <name>=<app1,app2,...>")
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

  alias <name>=<cmd> - Add a custom alias (e.g., alias ff=firefox)
  aliases        - List all aliases
  unalias <name> - Remove an alias

  group <name>   - Launch an app group (e.g., group dev)
  groups         - List all groups
  create-group <name>=<app1,app2> - Create a group

  help           - Show this help
  stats          - Show usage statistics
  frequent       - Show frequently used apps
  quit/exit      - Exit interactive mode

Examples:
  > open firefox
  > launch vs code
  > start terminal
  > run spotify
  > ff           (opens Firefox if alias exists)
  > alias code=code
  > code         (opens VS Code)
  > group dev    (launches dev workspace)
  > groups       (list all groups)
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
        """,
    )

    parser.add_argument(
        "command", nargs="?", help="Natural language command (e.g., 'open firefox')"
    )
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("-v", "--voice", action="store_true", help="Enable voice input mode")
    parser.add_argument("-s", "--suggest", metavar="QUERY", help="Get app suggestions for a query")
    parser.add_argument("--list-apps", action="store_true", help="List detected applications")
    parser.add_argument("--config", action="store_true", help="Show/edit configuration")
    parser.add_argument(
        "--provider",
        choices=["ollama", "gemini", "openai", "openrouter"],
        help="Override AI provider",
    )
    parser.add_argument(
        "--no-notifications", action="store_true", help="Disable system notifications"
    )
    parser.add_argument("--no-history", action="store_true", help="Disable usage history")
    parser.add_argument("--gui", action="store_true", help="Open GUI interface")
    parser.add_argument("--tray", action="store_true", help="Run in system tray mode")
    parser.add_argument(
        "--shortcut", action="store_true", help="Enable global keyboard shortcut (Ctrl+Alt+Space)"
    )
    parser.add_argument(
        "--shortcut-key",
        type=str,
        default="<ctrl><alt>space",
        help="Custom keyboard shortcut (default: <ctrl><alt>space)",
    )
    parser.add_argument("--setup", action="store_true", help="Run first-time setup wizard")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set logging level",
    )
    parser.add_argument(
        "--web-search",
        metavar="QUERY",
        help="Search the web for an application (fallback when app not found)",
    )
    parser.add_argument(
        "--alias",
        metavar="NAME=COMMAND",
        help="Add a custom alias (e.g., --alias 'ff=firefox')",
    )
    parser.add_argument(
        "--list-aliases", action="store_true", help="List all custom aliases"
    )
    parser.add_argument(
        "--remove-alias",
        metavar="NAME",
        help="Remove a custom alias",
    )
    parser.add_argument(
        "--group",
        metavar="NAME",
        help="Launch an app group/workspace (e.g., --group dev)",
    )
    parser.add_argument(
        "--create-group",
        metavar="NAME=APP1,APP2,...",
        help="Create a new app group (e.g., --create-group 'mygroup=code,firefox,term')",
    )
    parser.add_argument(
        "--list-groups", action="store_true", help="List all app groups"
    )
    parser.add_argument(
        "--remove-group",
        metavar="NAME",
        help="Remove an app group",
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

    # Handle --web-search
    if args.web_search:
        web_searcher = WebSearcher()
        print(f"Searching web for '{args.web_search}'...")
        url = web_searcher.search_app(args.web_search)
        if url:
            print(f"Search URL: {url}")
        return

    # Handle --alias
    if args.alias:
        alias_manager = AliasManager()
        if "=" not in args.alias:
            print("Error: Alias must be in format NAME=COMMAND")
            return
        name, command = args.alias.split("=", 1)
        if alias_manager.add_alias(name.strip(), command.strip()):
            print(f"Added alias: {name.strip()} -> {command.strip()}")
        else:
            print(f"Alias '{name.strip()}' already exists")
        return

    # Handle --list-aliases
    if args.list_aliases:
        alias_manager = AliasManager()
        aliases = alias_manager.list_aliases()
        print(f"Custom aliases ({len(aliases)} total):")
        for alias in aliases:
            tags = f" [{', '.join(alias.tags)}]" if alias.tags else ""
            desc = f" - {alias.description}" if alias.description else ""
            print(f"  {alias.name} -> {alias.command}{tags}{desc}")
        return

    # Handle --remove-alias
    if args.remove_alias:
        alias_manager = AliasManager()
        if alias_manager.remove_alias(args.remove_alias):
            print(f"Removed alias: {args.remove_alias}")
        else:
            print(f"Could not remove alias '{args.remove_alias}' (may be a default alias)")
        return

    # Handle --group
    if args.group:
        group_manager = GroupManager()
        print(f"Launching group: {args.group}")
        success, results = group_manager.launch_group(args.group, executor)
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.app_name}: {result.message}")
        return

    # Handle --create-group
    if args.create_group:
        group_manager = GroupManager()
        if "=" not in args.create_group:
            print("Error: Group must be in format NAME=APP1,APP2,...")
            return
        name, apps_str = args.create_group.split("=", 1)
        apps = [app.strip() for app in apps_str.split(",")]
        if group_manager.add_group(name.strip(), apps):
            print(f"Created group: {name.strip()} ({len(apps)} apps)")
        else:
            print(f"Group '{name.strip()}' already exists")
        return

    # Handle --list-groups
    if args.list_groups:
        group_manager = GroupManager()
        groups = group_manager.list_groups()
        print(f"App groups ({len(groups)} total):")
        for group in groups:
            apps = ", ".join(group.apps)
            desc = f" - {group.description}" if group.description else ""
            print(f"  {group.name}: {apps}{desc}")
        return

    # Handle --remove-group
    if args.remove_group:
        group_manager = GroupManager()
        if group_manager.remove_group(args.remove_group):
            print(f"Removed group: {args.remove_group}")
        else:
            print(f"Could not remove group '{args.remove_group}' (may be a default group)")
        return

    # Handle --suggest
    if args.suggest:
        apps = detector.detect()
        app_names = [app.name for app in apps]

        if ai_provider.is_available():
            try:
                suggestions = ai_provider.suggest_apps(
                    args.suggest, app_names, config.get().max_suggestions
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
        for i, (name, score) in enumerate(matches[: config.get().max_suggestions], 1):
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
