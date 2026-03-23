"""Extended tests for remaining modules to increase coverage."""

import unittest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestCategoriesExtended(unittest.TestCase):
    """Extended tests for categories module."""

    def test_app_category_enum_all_values(self):
        """Test all AppCategory enum values."""
        from aipp_opener.categories import AppCategory

        categories = [
            AppCategory.BROWSER, AppCategory.EDITOR, AppCategory.IDE,
            AppCategory.TERMINAL, AppCategory.MEDIA, AppCategory.VIDEO,
            AppCategory.AUDIO, AppCategory.GRAPHICS, AppCategory.OFFICE,
            AppCategory.COMMUNICATION, AppCategory.GAME, AppCategory.SYSTEM,
            AppCategory.UTILITY, AppCategory.DEVELOPMENT, AppCategory.OTHER
        ]
        self.assertEqual(len(categories), 15)

    def test_categorize_partial_matches(self):
        """Test categorizing with partial name matches."""
        from aipp_opener.categories import AppCategorizer

        categorizer = AppCategorizer()
        
        # Test partial matches
        category = categorizer.categorize("firefox-developer")
        self.assertEqual(category.value, "browser")
        
        category = categorizer.categorize("code-oss")
        self.assertEqual(category.value, "ide")

    def test_categorize_from_desktop_categories(self):
        """Test categorizing from desktop file categories."""
        from aipp_opener.categories import AppCategorizer

        categorizer = AppCategorizer()
        
        # Test various desktop categories
        category = categorizer.categorize("unknown", ["AudioVideo"])
        self.assertEqual(category.value, "media")
        
        category = categorizer.categorize("unknown", ["Audio"])
        self.assertEqual(category.value, "audio")
        
        category = categorizer.categorize("unknown", ["Video"])
        self.assertEqual(category.value, "video")
        
        category = categorizer.categorize("unknown", ["Graphics"])
        self.assertEqual(category.value, "graphics")
        
        category = categorizer.categorize("unknown", ["Network"])
        self.assertEqual(category.value, "communication")
        
        category = categorizer.categorize("unknown", ["Game"])
        self.assertEqual(category.value, "game")
        
        category = categorizer.categorize("unknown", ["Settings"])
        self.assertEqual(category.value, "system")

    def test_filter_by_category_empty(self):
        """Test filtering with no matches."""
        from aipp_opener.categories import AppCategorizer, AppCategory
        from aipp_opener.detectors.base import AppInfo

        categorizer = AppCategorizer()
        apps = [
            AppInfo(name="firefox", executable="/usr/bin/firefox"),
        ]
        
        result = categorizer.filter_by_category(apps, AppCategory.IDE)
        self.assertIsInstance(result, list)

    def test_get_category_counts_empty(self):
        """Test getting counts for empty list."""
        from aipp_opener.categories import AppCategorizer

        categorizer = AppCategorizer()
        counts = categorizer.get_category_counts([])
        self.assertIsInstance(counts, dict)

    def test_get_categories_summary_empty(self):
        """Test getting summary for empty list."""
        from aipp_opener.categories import AppCategorizer

        categorizer = AppCategorizer()
        summary = categorizer.get_categories_summary([])
        self.assertEqual(summary, [])


class TestCacheExtended(unittest.TestCase):
    """Extended tests for cache module."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.cache import Cache
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = Cache(name="test", cache_dir=Path(self.temp_dir.name), ttl=60)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_app_detection_cache_clear(self):
        """Test app detection cache clear."""
        from aipp_opener.cache import AppDetectionCache
        
        cache = AppDetectionCache(ttl=60)
        cache.set_apps("test", [{"name": "test"}])
        cache.clear()
        
        result = cache.get_apps("test")
        self.assertIsNone(result)


class TestIconsExtended(unittest.TestCase):
    """Extended tests for icons module."""

    def test_icon_info_dataclass(self):
        """Test IconInfo dataclass."""
        from aipp_opener.icons import IconInfo
        
        icon = IconInfo(name="test", path="/test/path")
        self.assertEqual(icon.name, "test")
        self.assertEqual(icon.path, "/test/path")

    def test_icon_finder_find_by_name(self):
        """Test finding icon by name."""
        from aipp_opener.icons import IconFinder
        
        finder = IconFinder()
        result = finder._find_by_name("firefox")
        self.assertIsNotNone(result)


class TestAliasesExtended(unittest.TestCase):
    """Extended tests for aliases module."""

    def test_custom_command_dataclass(self):
        """Test CustomCommand dataclass."""
        from aipp_opener.aliases import CustomCommand
        
        cmd = CustomCommand(
            name="test",
            command="echo test",
            description="Test command",
            tags=["test"]
        )
        self.assertEqual(cmd.name, "test")
        self.assertEqual(cmd.command, "echo test")

    def test_alias_manager_remove_nonexistent(self):
        """Test removing nonexistent alias."""
        from aipp_opener.aliases import AliasManager
        
        manager = AliasManager()
        result = manager.remove_alias("nonexistent")
        self.assertFalse(result)

    def test_alias_manager_list_aliases(self):
        """Test listing all aliases."""
        from aipp_opener.aliases import AliasManager
        
        manager = AliasManager()
        manager.add_alias("test1", "command1")
        manager.add_alias("test2", "command2")
        
        aliases = manager.list_aliases()
        self.assertIsInstance(aliases, list)
        self.assertGreater(len(aliases), 0)


class TestGroupsExtended(unittest.TestCase):
    """Extended tests for groups module."""

    def test_app_group_to_dict(self):
        """Test AppGroup to_dict method."""
        from aipp_opener.groups import AppGroup
        
        group = AppGroup(
            name="test",
            apps=["app1", "app2"],
            description="Test group"
        )
        data = group.to_dict()
        
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["apps"], ["app1", "app2"])

    def test_app_group_from_dict(self):
        """Test AppGroup from_dict method."""
        from aipp_opener.groups import AppGroup
        
        data = {
            "name": "test",
            "apps": ["app1", "app2"],
            "description": "Test group"
        }
        group = AppGroup.from_dict(data)
        
        self.assertEqual(group.name, "test")
        self.assertEqual(group.apps, ["app1", "app2"])

    def test_group_manager_update_group(self):
        """Test updating a group."""
        from aipp_opener.groups import GroupManager
        
        manager = GroupManager()
        manager.add_group("test", ["app1"])
        manager.update_group("test", ["app1", "app2"])
        
        group = manager.get_group("test")
        self.assertIn("app2", group.apps)


class TestAsyncWebSearchExtended(unittest.TestCase):
    """Extended tests for async web search module."""

    def test_async_searcher_init(self):
        """Test async web searcher initialization."""
        from aipp_opener.async_web_search import AsyncWebSearcher
        
        searcher = AsyncWebSearcher()
        self.assertIsNotNone(searcher)

    def test_async_searcher_engines(self):
        """Test async web searcher engines."""
        from aipp_opener.async_web_search import AsyncWebSearcher
        
        searcher = AsyncWebSearcher()
        engines = searcher.get_available_engines()
        self.assertIsInstance(engines, list)


class TestContextAwareSuggesterExtended(unittest.TestCase):
    """Extended tests for context aware suggester module."""

    def test_suggester_init(self):
        """Test suggester initialization."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester
        
        suggester = ContextAwareSuggester()
        self.assertIsNotNone(suggester)

    def test_suggester_get_suggestions(self):
        """Test getting suggestions."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester

        suggester = ContextAwareSuggester()
        # Just test the method exists and returns a list
        suggestions = suggester.get_suggestions()
        self.assertIsInstance(suggestions, list)


class TestAIChatExtended(unittest.TestCase):
    """Extended tests for AI chat module."""

    def test_chat_assistant_init(self):
        """Test chat assistant initialization."""
        from aipp_opener.ai_chat import AIChatAssistant
        
        mock_provider = MagicMock()
        mock_provider.name = "ollama"
        
        assistant = AIChatAssistant(mock_provider)
        self.assertIsNotNone(assistant)

    def test_chat_assistant_build_messages(self):
        """Test building messages."""
        from aipp_opener.ai_chat import AIChatAssistant
        
        mock_provider = MagicMock()
        mock_provider.name = "ollama"
        
        assistant = AIChatAssistant(mock_provider)
        messages = assistant._build_messages("test message")
        
        self.assertIsInstance(messages, list)
        self.assertGreater(len(messages), 0)

    def test_chat_assistant_format_context(self):
        """Test formatting context."""
        from aipp_opener.ai_chat import AIChatAssistant
        from aipp_opener.context_aware_suggester import ContextState
        
        mock_provider = MagicMock()
        mock_provider.name = "ollama"
        
        assistant = AIChatAssistant(mock_provider)
        context = ContextState(
            current_hour=10,
            current_day=0,
            is_work_hours=True,
            is_weekend=False,
            recent_apps=["code"]
        )
        
        formatted = assistant._format_context(context)
        self.assertIsInstance(formatted, str)

    def test_chat_assistant_clear_history(self):
        """Test clearing history."""
        from aipp_opener.ai_chat import AIChatAssistant
        
        mock_provider = MagicMock()
        mock_provider.name = "ollama"
        
        assistant = AIChatAssistant(mock_provider)
        assistant._conversation_history = [{"role": "user", "content": "test"}]
        assistant.clear_history()
        
        self.assertEqual(len(assistant._conversation_history), 0)


if __name__ == "__main__":
    unittest.main()
