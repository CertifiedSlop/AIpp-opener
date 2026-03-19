"""Plugin system for AIpp Opener."""

import importlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from aipp_opener.logger_config import get_logger

if TYPE_CHECKING:
    from aipp_opener.detectors.base import AppInfo
    from aipp_opener.executor import ExecutionResult

logger = get_logger(__name__)


class Plugin(ABC):
    """Base class for all AIpp Opener plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""
        pass

    @property
    def description(self) -> str:
        """Return the plugin description."""
        return ""

    def on_load(self) -> None:
        """Called when the plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        pass


class AppDetectorPlugin(Plugin):
    """Plugin that adds app detection capabilities."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this detector is available on the current system."""
        pass

    @abstractmethod
    def detect(self) -> list["AppInfo"]:
        """Detect applications on the system."""
        pass


class CommandPlugin(Plugin):
    """Plugin that adds custom commands."""

    @abstractmethod
    def get_commands(self) -> dict[str, callable]:
        """Return a dict of command names to callables."""
        pass


class ResultModifierPlugin(Plugin):
    """Plugin that modifies execution results."""

    @abstractmethod
    def modify_result(self, result: "ExecutionResult") -> "ExecutionResult":
        """Modify an execution result."""
        pass


class PluginManager:
    """Manages loading and unloading of plugins."""

    DEFAULT_PLUGIN_DIR = Path.home() / ".local" / "share" / "aipp_opener" / "plugins"

    def __init__(self, plugin_dir: Optional[Path] = None):
        """
        Initialize the plugin manager.

        Args:
            plugin_dir: Directory containing plugins.
        """
        self.plugin_dir = plugin_dir or self.DEFAULT_PLUGIN_DIR
        self._plugins: dict[str, Plugin] = {}
        self._plugin_configs: dict[str, dict] = {}
        self._load_plugin_list()

    def _load_plugin_list(self) -> None:
        """Load list of enabled plugins from config."""
        config_file = self.plugin_dir.parent / "plugins.json"

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    self._plugin_configs = data.get("plugins", {})
                logger.debug("Loaded plugin config: %s", list(self._plugin_configs.keys()))
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Could not load plugin config: %s", e)
                self._plugin_configs = {}
        else:
            self._plugin_configs = {}

    def _save_plugin_list(self) -> None:
        """Save list of enabled plugins to config."""
        self.plugin_dir.parent.mkdir(parents=True, exist_ok=True)
        config_file = self.plugin_dir.parent / "plugins.json"

        with open(config_file, "w") as f:
            json.dump({"plugins": self._plugin_configs}, f, indent=2)

    def register_plugin(self, plugin: Plugin, enabled: bool = True) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register.
            enabled: Whether the plugin is enabled.
        """
        self._plugins[plugin.name] = plugin
        self._plugin_configs[plugin.name] = {"enabled": enabled}
        self._save_plugin_list()

        if enabled:
            try:
                plugin.on_load()
                logger.info("Plugin loaded: %s (v%s)", plugin.name, plugin.version)
            except Exception as e:
                logger.error("Error loading plugin %s: %s", plugin.name, e)
                del self._plugins[plugin.name]

    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin by name.

        Args:
            name: Name of the plugin.

        Returns:
            True if unregistered, False if not found.
        """
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]
        try:
            plugin.on_unload()
        except Exception as e:
            logger.error("Error unloading plugin %s: %s", name, e)

        del self._plugins[name]
        if name in self._plugin_configs:
            del self._plugin_configs[name]
            self._save_plugin_list()

        logger.info("Plugin unloaded: %s", name)
        return True

    def load_plugin_from_file(self, plugin_file: Path) -> Optional[Plugin]:
        """
        Load a plugin from a Python file.

        Args:
            plugin_file: Path to the plugin file.

        Returns:
            Loaded plugin or None if loading failed.
        """
        if not plugin_file.exists():
            logger.error("Plugin file not found: %s", plugin_file)
            return None

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_file.stem}", plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class (first subclass of Plugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin
                ):
                    plugin_class = attr
                    break

            if plugin_class:
                plugin = plugin_class()
                enabled = self._plugin_configs.get(plugin.name, {}).get("enabled", True)
                self.register_plugin(plugin, enabled)
                return plugin

            logger.error("No plugin class found in %s", plugin_file)
            return None

        except Exception as e:
            logger.error("Error loading plugin from %s: %s", plugin_file, e)
            return None

    def load_all_plugins(self) -> int:
        """
        Load all plugins from the plugin directory.

        Returns:
            Number of plugins loaded.
        """
        loaded = 0

        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return loaded

        for plugin_file in self.plugin_dir.glob("*.py"):
            if self.load_plugin_from_file(plugin_file):
                loaded += 1

        logger.info("Loaded %d plugins", loaded)
        return loaded

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Get a plugin by name.

        Args:
            name: Name of the plugin.

        Returns:
            Plugin instance or None.
        """
        return self._plugins.get(name)

    def get_all_plugins(self) -> list[Plugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> list[Plugin]:
        """Get all enabled plugins."""
        return [
            p for p in self._plugins.values()
            if self._plugin_configs.get(p.name, {}).get("enabled", True)
        ]

    def get_detector_plugins(self) -> list[AppDetectorPlugin]:
        """Get all detector plugins."""
        return [
            p for p in self.get_enabled_plugins()
            if isinstance(p, AppDetectorPlugin)
        ]

    def get_command_plugins(self) -> list[CommandPlugin]:
        """Get all command plugins."""
        return [
            p for p in self.get_enabled_plugins()
            if isinstance(p, CommandPlugin)
        ]

    def get_result_modifier_plugins(self) -> list[ResultModifierPlugin]:
        """Get all result modifier plugins."""
        return [
            p for p in self.get_enabled_plugins()
            if isinstance(p, ResultModifierPlugin)
        ]

    def list_available_commands(self) -> dict[str, callable]:
        """Get all commands from command plugins."""
        commands = {}
        for plugin in self.get_command_plugins():
            try:
                plugin_commands = plugin.get_commands()
                commands.update(plugin_commands)
            except Exception as e:
                logger.error("Error getting commands from plugin %s: %s", plugin.name, e)
        return commands

    def get_plugin_info(self, name: str) -> Optional[dict]:
        """
        Get information about a plugin.

        Args:
            name: Plugin name.

        Returns:
            Dict with plugin info or None.
        """
        plugin = self.get_plugin(name)
        if not plugin:
            return None

        return {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "enabled": self._plugin_configs.get(name, {}).get("enabled", True),
            "type": plugin.__class__.__bases__[0].__name__,
        }

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if name not in self._plugin_configs:
            return False

        self._plugin_configs[name]["enabled"] = True
        self._save_plugin_list()

        plugin = self.get_plugin(name)
        if plugin:
            try:
                plugin.on_load()
                logger.info("Plugin enabled: %s", name)
            except Exception as e:
                logger.error("Error enabling plugin %s: %s", name, e)
                return False

        return True

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        if name not in self._plugin_configs:
            return False

        plugin = self.get_plugin(name)
        if plugin:
            try:
                plugin.on_unload()
                logger.info("Plugin disabled: %s", name)
            except Exception as e:
                logger.error("Error disabling plugin %s: %s", name, e)

        self._plugin_configs[name]["enabled"] = False
        self._save_plugin_list()
        return True

    def get_stats(self) -> dict:
        """Get plugin statistics."""
        return {
            "total_plugins": len(self._plugins),
            "enabled_plugins": len(self.get_enabled_plugins()),
            "detector_plugins": len(self.get_detector_plugins()),
            "command_plugins": len(self.get_command_plugins()),
            "result_modifier_plugins": len(self.get_result_modifier_plugins()),
        }
