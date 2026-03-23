"""Tests for plugins module."""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestPluginSecurityLevel(unittest.TestCase):
    """Tests for PluginSecurityLevel enum."""

    def test_security_levels_exist(self):
        """Test that all security levels are defined."""
        from aipp_opener.plugins import PluginSecurityLevel

        self.assertEqual(PluginSecurityLevel.SANDBOXED.value, "sandboxed")
        self.assertEqual(PluginSecurityLevel.RESTRICTED.value, "restricted")
        self.assertEqual(PluginSecurityLevel.TRUSTED.value, "trusted")


class TestPluginMetadata(unittest.TestCase):
    """Tests for PluginMetadata dataclass."""

    def test_plugin_metadata_minimal(self):
        """Test PluginMetadata with minimal fields."""
        from aipp_opener.plugins import PluginMetadata, PluginSecurityLevel

        meta = PluginMetadata(name="test-plugin", version="1.0.0")
        self.assertEqual(meta.name, "test-plugin")
        self.assertEqual(meta.version, "1.0.0")
        self.assertEqual(meta.description, "")
        self.assertEqual(meta.author, "")
        self.assertEqual(meta.security_level, PluginSecurityLevel.RESTRICTED)
        self.assertEqual(meta.permissions, set())
        self.assertIsNone(meta.file_hash)
        self.assertFalse(meta.is_verified)

    def test_plugin_metadata_full(self):
        """Test PluginMetadata with all fields."""
        from aipp_opener.plugins import PluginMetadata, PluginSecurityLevel

        meta = PluginMetadata(
            name="full-plugin",
            version="2.0.0",
            description="A test plugin",
            author="Test Author",
            security_level=PluginSecurityLevel.TRUSTED,
            permissions={"read", "write"},
            file_hash="abc123",
            is_verified=True
        )
        self.assertEqual(meta.name, "full-plugin")
        self.assertEqual(meta.version, "2.0.0")
        self.assertEqual(meta.description, "A test plugin")
        self.assertEqual(meta.author, "Test Author")
        self.assertEqual(meta.security_level, PluginSecurityLevel.TRUSTED)
        self.assertEqual(meta.permissions, {"read", "write"})
        self.assertEqual(meta.file_hash, "abc123")
        self.assertTrue(meta.is_verified)

    def test_plugin_metadata_to_dict(self):
        """Test PluginMetadata conversion to dict."""
        from aipp_opener.plugins import PluginMetadata, PluginSecurityLevel

        meta = PluginMetadata(
            name="test",
            version="1.0",
            description="Test",
            author="Author",
            security_level=PluginSecurityLevel.SANDBOXED,
            permissions={"read"},
            file_hash="hash",
            is_verified=True
        )
        data = meta.to_dict()

        self.assertEqual(data["name"], "test")
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["description"], "Test")
        self.assertEqual(data["author"], "Author")
        self.assertEqual(data["security_level"], "sandboxed")
        self.assertEqual(data["permissions"], ["read"])
        self.assertEqual(data["file_hash"], "hash")
        self.assertTrue(data["is_verified"])

    def test_plugin_metadata_from_dict(self):
        """Test PluginMetadata creation from dict."""
        from aipp_opener.plugins import PluginMetadata, PluginSecurityLevel

        data = {
            "name": "test",
            "version": "1.0",
            "description": "Test",
            "author": "Author",
            "security_level": "trusted",
            "permissions": ["read", "write"],
            "file_hash": "hash",
            "is_verified": True
        }
        meta = PluginMetadata.from_dict(data)

        self.assertEqual(meta.name, "test")
        self.assertEqual(meta.version, "1.0")
        self.assertEqual(meta.security_level, PluginSecurityLevel.TRUSTED)
        self.assertEqual(meta.permissions, {"read", "write"})
        self.assertTrue(meta.is_verified)

    def test_plugin_metadata_from_dict_defaults(self):
        """Test PluginMetadata from dict with missing fields."""
        from aipp_opener.plugins import PluginMetadata, PluginSecurityLevel

        data = {"name": "test", "version": "1.0"}
        meta = PluginMetadata.from_dict(data)

        self.assertEqual(meta.name, "test")
        self.assertEqual(meta.version, "1.0")
        self.assertEqual(meta.description, "")
        self.assertEqual(meta.author, "")
        self.assertEqual(meta.security_level, PluginSecurityLevel.RESTRICTED)
        self.assertEqual(meta.permissions, set())
        self.assertFalse(meta.is_verified)


class TestPluginBase(unittest.TestCase):
    """Tests for Plugin abstract base class."""

    def test_plugin_is_abstract(self):
        """Test that Plugin cannot be instantiated directly."""
        from aipp_opener.plugins import Plugin

        with self.assertRaises(TypeError):
            Plugin()

    def test_plugin_subclass_must_implement_abstract_methods(self):
        """Test that Plugin subclasses must implement abstract methods."""
        from aipp_opener.plugins import Plugin

        class IncompletePlugin(Plugin):
            pass

        with self.assertRaises(TypeError):
            IncompletePlugin()

    def test_plugin_complete_subclass(self):
        """Test a complete Plugin implementation."""
        from aipp_opener.plugins import Plugin, PluginMetadata

        class CompletePlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

            def on_load(self) -> None:
                pass

            def on_unload(self) -> None:
                pass

        plugin = CompletePlugin()
        self.assertEqual(plugin.name, "test")
        self.assertEqual(plugin.version, "1.0")
        plugin.on_load()
        plugin.on_unload()

    def test_plugin_description_default(self):
        """Test that Plugin has default description."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.assertEqual(plugin.description, "")

    def test_plugin_metadata_default(self):
        """Test that Plugin has default metadata."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.assertIsNone(plugin.metadata)

    def test_plugin_validate_default(self):
        """Test that Plugin validate returns True by default."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        is_valid, error = plugin.validate()
        self.assertTrue(is_valid)
        self.assertEqual(error, "")


class TestAppDetectorPlugin(unittest.TestCase):
    """Tests for AppDetectorPlugin."""

    def test_app_detector_plugin_is_abstract(self):
        """Test that AppDetectorPlugin cannot be instantiated."""
        from aipp_opener.plugins import AppDetectorPlugin

        with self.assertRaises(TypeError):
            AppDetectorPlugin()

    def test_app_detector_plugin_complete(self):
        """Test complete AppDetectorPlugin implementation."""
        from aipp_opener.plugins import AppDetectorPlugin

        class TestDetectorPlugin(AppDetectorPlugin):
            @property
            def name(self) -> str:
                return "test-detector"

            @property
            def version(self) -> str:
                return "1.0"

            def is_available(self) -> bool:
                return True

            def detect(self):
                return []

        plugin = TestDetectorPlugin()
        self.assertEqual(plugin.name, "test-detector")
        self.assertTrue(plugin.is_available())
        self.assertEqual(plugin.detect(), [])


class TestCommandPlugin(unittest.TestCase):
    """Tests for CommandPlugin."""

    def test_command_plugin_is_abstract(self):
        """Test that CommandPlugin cannot be instantiated."""
        from aipp_opener.plugins import CommandPlugin

        with self.assertRaises(TypeError):
            CommandPlugin()

    def test_command_plugin_complete(self):
        """Test complete CommandPlugin implementation."""
        from aipp_opener.plugins import CommandPlugin

        class TestCommandPlugin(CommandPlugin):
            @property
            def name(self) -> str:
                return "test-command"

            @property
            def version(self) -> str:
                return "1.0"

            def get_commands(self):
                return {"test": lambda: "result"}

        plugin = TestCommandPlugin()
        commands = plugin.get_commands()
        self.assertIn("test", commands)


class TestResultModifierPlugin(unittest.TestCase):
    """Tests for ResultModifierPlugin."""

    def test_result_modifier_plugin_is_abstract(self):
        """Test that ResultModifierPlugin cannot be instantiated."""
        from aipp_opener.plugins import ResultModifierPlugin

        with self.assertRaises(TypeError):
            ResultModifierPlugin()


class TestPluginManager(unittest.TestCase):
    """Tests for PluginManager class."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.plugins import PluginManager

        self.temp_dir = tempfile.TemporaryDirectory()
        self.plugin_dir = Path(self.temp_dir.name)
        self.manager = PluginManager(plugin_dir=self.plugin_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_plugin_manager_init(self):
        """Test PluginManager initialization."""
        from aipp_opener.plugins import PluginManager

        manager = PluginManager()
        self.assertIsNotNone(manager)

    def test_plugin_manager_init_custom_dir(self):
        """Test PluginManager with custom plugin directory."""
        from aipp_opener.plugins import PluginManager

        manager = PluginManager(plugin_dir=self.plugin_dir)
        self.assertEqual(manager.plugin_dir, self.plugin_dir)

    def test_plugin_manager_default_plugin_dir(self):
        """Test PluginManager default plugin directory."""
        from aipp_opener.plugins import PluginManager

        manager = PluginManager()
        expected = Path.home() / ".local" / "share" / "aipp_opener" / "plugins"
        self.assertEqual(manager.plugin_dir, expected)

    def test_register_plugin(self):
        """Test registering a plugin."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.manager.register_plugin(plugin)

        self.assertIn("test", self.manager._plugins)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.manager.register_plugin(plugin)
        self.manager.unregister_plugin("test")

        self.assertNotIn("test", self.manager._plugins)

    def test_get_plugin(self):
        """Test getting a registered plugin."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.manager.register_plugin(plugin)

        retrieved = self.manager.get_plugin("test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "test")

    def test_get_plugin_not_found(self):
        """Test getting a plugin that doesn't exist."""
        plugin = self.manager.get_plugin("nonexistent")
        self.assertIsNone(plugin)

    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.manager.register_plugin(plugin)

        plugins = self.manager.get_all_plugins()
        self.assertGreater(len(plugins), 0)

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        plugins = self.manager.get_enabled_plugins()
        self.assertIsInstance(plugins, list)

    def test_get_plugin_info(self):
        """Test getting plugin info."""
        from aipp_opener.plugins import Plugin

        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0"

        plugin = TestPlugin()
        self.manager.register_plugin(plugin)

        info = self.manager.get_plugin_info("test")
        self.assertIsNotNone(info)

    def test_get_plugin_info_not_found(self):
        """Test getting info for non-existent plugin."""
        info = self.manager.get_plugin_info("nonexistent")
        self.assertIsNone(info)

    def test_verify_plugin(self):
        """Test verifying a plugin."""
        result = self.manager.verify_plugin("nonexistent", "expected_hash")
        self.assertFalse(result)

    def test_get_plugin_metadata(self):
        """Test getting plugin metadata."""
        meta = self.manager.get_plugin_metadata("nonexistent")
        self.assertIsNone(meta)

    def test_mark_plugin_verified(self):
        """Test marking a plugin as verified."""
        result = self.manager.mark_plugin_verified("test-plugin")
        self.assertIsInstance(result, bool)

    def test_list_unverified_plugins(self):
        """Test listing unverified plugins."""
        plugins = self.manager.list_unverified_plugins()
        self.assertIsInstance(plugins, list)

    def test_get_stats(self):
        """Test getting plugin manager stats."""
        stats = self.manager.get_stats()
        self.assertIsInstance(stats, dict)

    def test_get_detector_plugins(self):
        """Test getting detector plugins."""
        plugins = self.manager.get_detector_plugins()
        self.assertIsInstance(plugins, list)

    def test_get_command_plugins(self):
        """Test getting command plugins."""
        plugins = self.manager.get_command_plugins()
        self.assertIsInstance(plugins, list)

    def test_get_result_modifier_plugins(self):
        """Test getting result modifier plugins."""
        plugins = self.manager.get_result_modifier_plugins()
        self.assertIsInstance(plugins, list)

    def test_list_available_commands(self):
        """Test listing available commands from plugins."""
        commands = self.manager.list_available_commands()
        self.assertIsInstance(commands, dict)


if __name__ == "__main__":
    unittest.main()
