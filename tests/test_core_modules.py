"""Tests for AIpp Opener core modules."""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCache(unittest.TestCase):
    """Test the caching layer (aipp_opener/cache.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.cache import Cache, AppDetectionCache

        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = Cache(name="test_cache", cache_dir=Path(self.temp_dir.name), ttl=60)
        self.app_cache = AppDetectionCache(ttl=60)
        # Override cache file location for testing
        self.app_cache.cache_file = Path(self.temp_dir.name) / "app_detection.json"

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
        from aipp_opener.cache import Cache
        short_ttl_cache = Cache(name="test_ttl", cache_dir=Path(self.temp_dir.name), ttl=1)
        short_ttl_cache.set("expiring_key", {"data": "value"})

        time.sleep(1.5)

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

        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
        self.assertIsNone(self.cache.get("key3"))

    def test_app_detection_cache_set_apps(self):
        """Test setting apps in app detection cache."""
        apps = [
            {"name": "firefox", "executable": "/usr/bin/firefox"},
            {"name": "chrome", "executable": "/usr/bin/chrome"},
        ]

        self.app_cache.set_apps("test_platform", apps)
        result = self.app_cache.get_apps("test_platform")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "firefox")

    def test_app_detection_cache_different_platforms(self):
        """Test caching for different platforms."""
        nixos_apps = [{"name": "nix-app", "executable": "/nix/bin/app"}]
        debian_apps = [{"name": "deb-app", "executable": "/usr/bin/app"}]

        self.app_cache.set_apps("nixos", nixos_apps)
        self.app_cache.set_apps("debian", debian_apps)

        nixos_result = self.app_cache.get_apps("nixos")
        debian_result = self.app_cache.get_apps("debian")

        self.assertEqual(len(nixos_result), 1)
        self.assertEqual(nixos_result[0]["name"], "nix-app")
        self.assertEqual(len(debian_result), 1)
        self.assertEqual(debian_result[0]["name"], "deb-app")

    def test_cache_file_persistence(self):
        """Test that cache persists to file."""
        from aipp_opener.cache import Cache

        self.cache.set("persistent_key", "persistent_value")

        # Create new cache instance with same file
        new_cache = Cache(name="test_cache", cache_dir=Path(self.temp_dir.name), ttl=60)
        result = new_cache.get("persistent_key")

        self.assertEqual(result, "persistent_value")


class TestAliases(unittest.TestCase):
    """Test the aliases system (aipp_opener/aliases.py)."""

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
        alias_names = [a.name for a in aliases]
        self.assertIn("ff2", alias_names)
        self.assertIn("chrome2", alias_names)

    def test_default_aliases(self):
        """Test default aliases are loaded."""
        fresh_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        fresh_file.close()

        from aipp_opener.aliases import AliasManager
        manager = AliasManager(config_path=Path(fresh_file.name))
        aliases = manager.list_aliases()

        self.assertGreater(len(aliases), 0)

        Path(fresh_file.name).unlink(missing_ok=True)

    def test_alias_persistence(self):
        """Test aliases persist across manager instances."""
        self.manager.add_alias("persistent", "persistent_value")

        from aipp_opener.aliases import AliasManager
        new_manager = AliasManager(config_path=Path(self.temp_file.name))
        result = new_manager.get_alias("persistent")

        self.assertEqual(result.command, "persistent_value")

    def test_add_duplicate_alias(self):
        """Test that adding duplicate alias returns False."""
        self.manager.add_alias("dup", "duplicate")
        result = self.manager.add_alias("dup", "duplicate2")

        self.assertFalse(result)

    def test_custom_command_to_dict(self):
        """Test CustomCommand serialization."""
        from aipp_opener.aliases import CustomCommand

        cmd = CustomCommand(
            name="test",
            command="test_command",
            description="Test description",
            tags=["test", "demo"]
        )

        data = cmd.to_dict()

        self.assertEqual(data["name"], "test")
        self.assertEqual(data["command"], "test_command")
        self.assertEqual(data["description"], "Test description")
        self.assertEqual(data["tags"], ["test", "demo"])

    def test_custom_command_from_dict(self):
        """Test CustomCommand deserialization."""
        from aipp_opener.aliases import CustomCommand

        data = {
            "name": "test",
            "command": "test_command",
            "description": "Test description",
            "tags": ["test", "demo"]
        }

        cmd = CustomCommand.from_dict(data)

        self.assertEqual(cmd.name, "test")
        self.assertEqual(cmd.command, "test_command")
        self.assertEqual(cmd.description, "Test description")
        self.assertEqual(cmd.tags, ["test", "demo"])


class TestGroups(unittest.TestCase):
    """Test app groups/workspaces (aipp_opener/groups.py)."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.groups import GroupManager

        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = GroupManager(config_path=Path(self.temp_file.name))

    def tearDown(self):
        """Clean up test fixtures."""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_add_group(self):
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

    def test_app_group_to_dict(self):
        """Test AppGroup serialization."""
        from aipp_opener.groups import AppGroup

        group = AppGroup(
            name="test",
            apps=["app1", "app2"],
            description="Test group",
            delay=1.5
        )

        data = group.to_dict()

        self.assertEqual(data["name"], "test")
        self.assertEqual(data["apps"], ["app1", "app2"])
        self.assertEqual(data["description"], "Test group")
        self.assertEqual(data["delay"], 1.5)

    def test_app_group_from_dict(self):
        """Test AppGroup deserialization."""
        from aipp_opener.groups import AppGroup

        data = {
            "name": "test",
            "apps": ["app1", "app2"],
            "description": "Test group",
            "delay": 1.5
        }

        group = AppGroup.from_dict(data)

        self.assertEqual(group.name, "test")
        self.assertEqual(group.apps, ["app1", "app2"])
        self.assertEqual(group.description, "Test group")
        self.assertEqual(group.delay, 1.5)

    def test_add_duplicate_group(self):
        """Test that adding duplicate group returns False."""
        self.manager.add_group("dup", ["app1"])
        result = self.manager.add_group("dup", ["app2"])

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
