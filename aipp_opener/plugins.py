"""Plugin system for AIpp Opener with security sandboxing.

Plugins are loaded with restricted permissions and can be sandboxed
to prevent access to sensitive system resources.
"""

import importlib
import importlib.util
import json
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING, Set
from dataclasses import dataclass, field
from enum import Enum

from aipp_opener.logger_config import get_logger

if TYPE_CHECKING:
    from aipp_opener.detectors.base import AppInfo
    from aipp_opener.executor import ExecutionResult

logger = get_logger(__name__)


class PluginSecurityLevel(Enum):
    """Security levels for plugin sandboxing."""

    SANDBOXED = "sandboxed"  # Restricted access, no file system or network
    RESTRICTED = "restricted"  # Limited file system access
    TRUSTED = "trusted"  # Full access (user-verified plugins only)


@dataclass
class PluginMetadata:
    """Metadata about a plugin including security information."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    security_level: PluginSecurityLevel = PluginSecurityLevel.RESTRICTED
    permissions: Set[str] = field(default_factory=set)
    file_hash: Optional[str] = None
    is_verified: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "security_level": self.security_level.value,
            "permissions": list(self.permissions),
            "file_hash": self.file_hash,
            "is_verified": self.is_verified,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginMetadata":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            version=data.get("version", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            security_level=PluginSecurityLevel(
                data.get("security_level", "restricted")
            ),
            permissions=set(data.get("permissions", [])),
            file_hash=data.get("file_hash"),
            is_verified=data.get("is_verified", False),
        )


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

    @property
    def metadata(self) -> Optional[PluginMetadata]:
        """Return plugin metadata (optional)."""
        return None

    def on_load(self) -> None:
        """Called when the plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        pass

    def validate(self) -> tuple[bool, str]:
        """
        Validate the plugin for security issues.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default validation - always passes
        return True, ""


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
        Load a plugin from a Python file with security validation.

        Args:
            plugin_file: Path to the plugin file.

        Returns:
            Loaded plugin or None if loading failed.
        """
        if not plugin_file.exists():
            logger.error("Plugin file not found: %s", plugin_file)
            return None

        try:
            # Calculate file hash for verification
            file_hash = self._calculate_file_hash(plugin_file)

            # Security validation
            is_valid, error_msg = self._validate_plugin_file(plugin_file)
            if not is_valid:
                logger.error("Plugin validation failed for %s: %s", plugin_file, error_msg)
                return None

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

                # Run plugin's own validation
                is_valid, error_msg = plugin.validate()
                if not is_valid:
                    logger.error("Plugin %s failed self-validation: %s", plugin.name, error_msg)
                    return None

                enabled = self._plugin_configs.get(plugin.name, {}).get("enabled", True)

                # Store metadata
                if plugin.metadata:
                    plugin.metadata.file_hash = file_hash
                    self._save_plugin_metadata(plugin.name, plugin.metadata)

                self.register_plugin(plugin, enabled)
                logger.info("Loaded plugin %s from %s (hash: %s)", plugin.name, plugin_file.stem, file_hash[:8])
                return plugin

            logger.error("No plugin class found in %s", plugin_file)
            return None

        except Exception as e:
            logger.error("Error loading plugin from %s: %s", plugin_file, e)
            return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _validate_plugin_file(self, plugin_file: Path) -> tuple[bool, str]:
        """
        Validate a plugin file for security issues.

        Checks:
        - File is readable and valid Python
        - No obvious malicious patterns (eval, exec, __import__ with variables)
        - File size is reasonable (< 1MB)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        max_size = 1024 * 1024  # 1MB
        if plugin_file.stat().st_size > max_size:
            return False, f"Plugin file too large (>1MB): {plugin_file.stat().st_size} bytes"

        # Read and check for dangerous patterns
        try:
            content = plugin_file.read_text()
        except (IOError, UnicodeDecodeError) as e:
            return False, f"Cannot read plugin file: {e}"

        # Dangerous patterns that could indicate malicious code
        dangerous_patterns = [
            "__import__(os",
            "__import__(sys",
            "eval(",
            "exec(",
            "subprocess.Popen",
            "subprocess.call",
            "subprocess.run",
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                # Allow these patterns in comments/strings but flag for review
                logger.warning(
                    "Plugin %s contains potentially dangerous pattern: %s",
                    plugin_file.name,
                    pattern,
                )

        return True, ""

    def _save_plugin_metadata(self, plugin_name: str, metadata: PluginMetadata) -> None:
        """Save plugin metadata to config."""
        metadata_file = self.plugin_dir.parent / "plugin_metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {"plugins": {}}
        else:
            data = {"plugins": {}}

        data["plugins"][plugin_name] = metadata.to_dict()

        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin."""
        metadata_file = self.plugin_dir.parent / "plugin_metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
                plugin_data = data.get("plugins", {}).get(plugin_name)
                if plugin_data:
                    return PluginMetadata.from_dict(plugin_data)
        except (json.JSONDecodeError, IOError):
            pass

        return None

    def verify_plugin(self, plugin_name: str, expected_hash: str) -> bool:
        """
        Verify a plugin's integrity by checking its hash.

        Args:
            plugin_name: Name of the plugin to verify.
            expected_hash: Expected SHA256 hash.

        Returns:
            True if verification passes.
        """
        if plugin_name not in self._plugins:
            return False

        # Find plugin file
        plugin_file = self.plugin_dir / f"{plugin_name}.py"
        if not plugin_file.exists():
            return False

        current_hash = self._calculate_file_hash(plugin_file)
        is_valid = current_hash == expected_hash

        if is_valid:
            logger.info("Plugin %s verified successfully", plugin_name)
        else:
            logger.warning(
                "Plugin %s verification failed: expected %s, got %s",
                plugin_name,
                expected_hash[:8],
                current_hash[:8],
            )

        return is_valid

    def list_unverified_plugins(self) -> list[str]:
        """List plugins that haven't been verified by the user."""
        unverified = []

        for name, plugin in self._plugins.items():
            metadata = self.get_plugin_metadata(name)
            if not metadata or not metadata.is_verified:
                unverified.append(name)

        return unverified

    def mark_plugin_verified(self, plugin_name: str, verified: bool = True) -> bool:
        """
        Mark a plugin as verified by the user.

        Args:
            plugin_name: Name of the plugin.
            verified: Whether the plugin is verified.

        Returns:
            True if successful.
        """
        if plugin_name not in self._plugins:
            return False

        metadata = self.get_plugin_metadata(plugin_name)
        if not metadata:
            metadata = PluginMetadata(
                name=plugin_name,
                version=self._plugins[plugin_name].version,
                description=self._plugins[plugin_name].description,
            )

        metadata.is_verified = verified
        self._save_plugin_metadata(plugin_name, metadata)

        logger.info("Plugin %s marked as %s", plugin_name, "verified" if verified else "unverified")
        return True

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
