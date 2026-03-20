"""Tests for new AIpp Opener modules (v0.4.0+)."""

import unittest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestCache(unittest.TestCase):
    """Test the caching layer."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.cache import Cache

        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = Cache(name="test_cache", cache_dir=Path(self.temp_dir.name), ttl=60)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_cache_set_get(self):
        """Test setting and getting cache values."""
        self.cache.set("test_key", {"data": "value"})
        result = self.cache.get("test_key")

        self.assertEqual(result, {"data": "value"})

    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)

    def test_cache_ttl(self):
        """Test cache TTL expiration."""
        # Create cache with very short TTL
        from aipp_opener.cache import Cache
        short_ttl_cache = Cache(name="test_ttl", cache_dir=Path(self.temp_dir.name), ttl=1)
        short_ttl_cache.set("expiring_key", {"data": "value"})

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        result = short_ttl_cache.get("expiring_key")
        self.assertIsNone(result)

    def test_cache_delete(self):
        """Test cache deletion."""
        self.cache.set("to_delete", {"data": "value"})
        self.cache.delete("to_delete")

        result = self.cache.get("to_delete")
        self.assertIsNone(result)

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        self.cache.clear()

        # All should be gone
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
        self.assertIsNone(self.cache.get("key3"))


class TestAliases(unittest.TestCase):
    """Test the aliases system."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.aliases import AliasManager

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = AliasManager(config_path=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_add_alias(self):
        """Test adding an alias."""
        self.manager.add_alias("ff", "firefox")
        result = self.manager.get_alias("ff")

        self.assertEqual(result.command, "firefox")

    def test_get_nonexistent_alias(self):
        """Test getting a nonexistent alias."""
        result = self.manager.get_alias("nonexistent")
        self.assertIsNone(result)

    def test_remove_alias(self):
        """Test removing an alias."""
        self.manager.add_alias("temp", "temperature")
        self.manager.remove_alias("temp")

        result = self.manager.get_alias("temp")
        self.assertIsNone(result)

    def test_list_aliases(self):
        """Test listing all aliases."""
        self.manager.add_alias("ff2", "firefox2")
        self.manager.add_alias("chrome2", "chromium2")

        aliases = self.manager.list_aliases()

        self.assertGreaterEqual(len(aliases), 2)
        # aliases is a list of CustomCommand objects
        alias_names = [a.name for a in aliases]
        self.assertIn("ff2", alias_names)
        self.assertIn("chrome2", alias_names)

    def test_default_aliases(self):
        """Test default aliases are loaded."""
        # Create new manager with fresh file
        fresh_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        fresh_file.close()

        from aipp_opener.aliases import AliasManager
        manager = AliasManager(config_path=Path(fresh_file.name))
        aliases = manager.list_aliases()

        # Should have default aliases
        self.assertGreater(len(aliases), 0)

        Path(fresh_file.name).unlink(missing_ok=True)

    def test_alias_persistence(self):
        """Test aliases persist across manager instances."""
        self.manager.add_alias("persistent", "persistent_value")

        # Create new manager with same file
        from aipp_opener.aliases import AliasManager
        new_manager = AliasManager(config_path=Path(self.temp_file.name))
        result = new_manager.get_alias("persistent")

        self.assertEqual(result.command, "persistent_value")


class TestGroups(unittest.TestCase):
    """Test app groups/workspaces."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.groups import GroupManager

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = GroupManager(config_path=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_create_group(self):
        """Test creating a group."""
        apps = ["firefox-custom", "code-custom"]
        self.manager.add_group("dev-custom", apps)

        group = self.manager.get_group("dev-custom")

        self.assertIsNotNone(group)
        self.assertEqual(group.apps, apps)

    def test_get_nonexistent_group(self):
        """Test getting a nonexistent group."""
        group = self.manager.get_group("nonexistent")
        self.assertIsNone(group)

    def test_remove_group(self):
        """Test removing a group."""
        self.manager.add_group("temp-test", ["app1"])
        self.manager.remove_group("temp-test")

        group = self.manager.get_group("temp-test")
        self.assertIsNone(group)

    def test_list_groups(self):
        """Test listing all groups."""
        self.manager.add_group("dev2", ["firefox", "code"])
        self.manager.add_group("browse2", ["firefox", "chrome"])

        groups = self.manager.list_groups()

        self.assertGreaterEqual(len(groups), 2)
        group_names = [g.name for g in groups]
        self.assertIn("dev2", group_names)
        self.assertIn("browse2", group_names)

    def test_default_groups(self):
        """Test default groups are loaded."""
        from aipp_opener.groups import GroupManager
        fresh_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        fresh_file.close()

        manager = GroupManager(config_path=Path(fresh_file.name))
        groups = manager.list_groups()

        # Should have default groups (dev, browse, media, office)
        self.assertGreaterEqual(len(groups), 4)
        group_names = [g.name for g in groups]
        self.assertIn("dev", group_names)

        Path(fresh_file.name).unlink(missing_ok=True)

    def test_group_with_delay(self):
        """Test group with launch delay."""
        apps = ["app1", "app2", "app3"]
        self.manager.add_group("delayed-test", apps, delay=2.0)

        group = self.manager.get_group("delayed-test")

        self.assertEqual(group.delay, 2.0)


class TestWebSearch(unittest.TestCase):
    """Test web search functionality."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.web_search import WebSearcher

        self.searcher = WebSearcher(default_engine="google")

    def test_search_url_generation(self):
        """Test search URL is generated correctly."""
        url = self.searcher.search("test query", open_browser=False)

        self.assertIn("google.com", url)
        self.assertTrue("test+query" in url or "test%20query" in url)

    def test_different_engines(self):
        """Test different search engines."""
        engines = ["google", "duckduckgo", "bing", "github", "archwiki"]

        for engine in engines:
            url = self.searcher.search("test", engine=engine, open_browser=False)
            self.assertIsNotNone(url)

    def test_invalid_engine(self):
        """Test invalid engine raises error."""
        with self.assertRaises(ValueError):
            self.searcher.search("test", engine="invalid_engine")

    def test_app_search(self):
        """Test app search."""
        url = self.searcher.search_app("vscode", open_browser=False)

        self.assertTrue("install+vscode+linux" in url or "install%20vscode%20linux" in url)

    def test_command_search(self):
        """Test command search."""
        url = self.searcher.search_command("list files", open_browser=False)

        self.assertTrue("linux+command" in url or "linux%20command" in url)

    def test_get_available_engines(self):
        """Test getting available engines."""
        engines = self.searcher.get_available_engines()

        self.assertIsInstance(engines, list)
        self.assertGreater(len(engines), 0)


class TestPlugins(unittest.TestCase):
    """Test plugin system."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.plugins import PluginManager
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = PluginManager(plugin_dir=Path(self.temp_dir.name))

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_register_plugin(self):
        """Test registering a plugin."""
        from aipp_opener.plugins import Plugin
        
        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test_plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
        
        plugin = TestPlugin()
        self.manager.register_plugin(plugin)
        
        retrieved = self.manager.get_plugin("test_plugin")
        self.assertEqual(retrieved, plugin)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        from aipp_opener.plugins import Plugin
        
        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test_plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
        
        plugin = TestPlugin()
        self.manager.register_plugin(plugin)
        self.manager.unregister_plugin("test_plugin")
        
        retrieved = self.manager.get_plugin("test_plugin")
        self.assertIsNone(retrieved)

    def test_get_all_plugins(self):
        """Test getting all plugins."""
        from aipp_opener.plugins import Plugin
        
        class TestPlugin1(Plugin):
            @property
            def name(self) -> str:
                return "test1"
            
            @property
            def version(self) -> str:
                return "1.0.0"
        
        class TestPlugin2(Plugin):
            @property
            def name(self) -> str:
                return "test2"
            
            @property
            def version(self) -> str:
                return "1.0.0"
        
        self.manager.register_plugin(TestPlugin1())
        self.manager.register_plugin(TestPlugin2())
        
        all_plugins = self.manager.get_all_plugins()
        self.assertEqual(len(all_plugins), 2)

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        from aipp_opener.plugins import Plugin
        
        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test_plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
        
        plugin = TestPlugin()
        self.manager.register_plugin(plugin, enabled=False)
        
        enabled = self.manager.get_enabled_plugins()
        self.assertEqual(len(enabled), 0)
        
        # Enable it
        self.manager.enable_plugin("test_plugin")
        enabled = self.manager.get_enabled_plugins()
        self.assertEqual(len(enabled), 1)

    def test_plugin_stats(self):
        """Test getting plugin statistics."""
        stats = self.manager.get_stats()
        
        self.assertIn("total_plugins", stats)
        self.assertIn("enabled_plugins", stats)
        self.assertIn("detector_plugins", stats)
        self.assertIn("command_plugins", stats)
        self.assertIn("result_modifier_plugins", stats)

    def test_plugin_info(self):
        """Test getting plugin info."""
        from aipp_opener.plugins import Plugin
        
        class TestPlugin(Plugin):
            @property
            def name(self) -> str:
                return "test_plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            @property
            def description(self) -> str:
                return "Test plugin description"
        
        plugin = TestPlugin()
        self.manager.register_plugin(plugin)
        
        info = self.manager.get_plugin_info("test_plugin")
        
        self.assertEqual(info["name"], "test_plugin")
        self.assertEqual(info["version"], "1.0.0")
        self.assertEqual(info["description"], "Test plugin description")


if __name__ == "__main__":
    unittest.main()
