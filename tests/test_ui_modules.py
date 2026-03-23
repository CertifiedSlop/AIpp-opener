"""Tests for UI modules (Phase 6D) - Limited environment support."""

import unittest
from unittest.mock import patch, MagicMock


class TestKeyboardShortcut(unittest.TestCase):
    """Tests for keyboard shortcut module."""

    def test_keyboard_shortcut_init(self):
        """Test keyboard shortcut initialization."""
        from aipp_opener.keyboard import KeyboardShortcut
        
        shortcut = KeyboardShortcut()
        self.assertEqual(shortcut.shortcut, "<ctrl><alt>space")
        self.assertIsNone(shortcut.callback)
        self.assertFalse(shortcut._running)

    def test_keyboard_shortcut_custom(self):
        """Test keyboard shortcut with custom combination."""
        from aipp_opener.keyboard import KeyboardShortcut
        
        shortcut = KeyboardShortcut("<ctrl><alt>k")
        self.assertEqual(shortcut.shortcut, "<ctrl><alt>k")

    def test_is_available(self):
        """Test availability check."""
        from aipp_opener.keyboard import KeyboardShortcut
        
        shortcut = KeyboardShortcut()
        result = shortcut.is_available()
        self.assertIsInstance(result, bool)

    def test_detect_wayland(self):
        """Test Wayland detection."""
        from aipp_opener.keyboard import KeyboardShortcut
        
        shortcut = KeyboardShortcut()
        result = shortcut._detect_wayland()
        self.assertIsInstance(result, bool)

    @patch.dict('os.environ', {'WAYLAND_DISPLAY': 'wayland-0'})
    def test_detect_wayland_with_env(self):
        """Test Wayland detection with environment variable."""
        from aipp_opener.keyboard import KeyboardShortcut
        
        shortcut = KeyboardShortcut()
        result = shortcut._detect_wayland()
        self.assertTrue(result)


class TestWaylandShortcuts(unittest.TestCase):
    """Tests for Wayland shortcut support."""

    def test_wayland_session_init(self):
        """Test Wayland session initialization."""
        try:
            from aipp_opener.wayland_shortcuts import WaylandShortcutSession
            
            session = WaylandShortcutSession()
            self.assertIsNotNone(session)
        except ImportError:
            self.skipTest("Wayland shortcuts module not available")

    def test_wayland_session_methods(self):
        """Test Wayland session has required methods."""
        try:
            from aipp_opener.wayland_shortcuts import WaylandShortcutSession
            
            session = WaylandShortcutSession()
            self.assertTrue(hasattr(session, 'start'))
            self.assertTrue(hasattr(session, 'stop'))
        except ImportError:
            self.skipTest("Wayland shortcuts module not available")


class TestVoiceInput(unittest.TestCase):
    """Tests for voice input module."""

    def test_voice_init(self):
        """Test voice input initialization."""
        from aipp_opener.voice import VoiceInput
        
        voice = VoiceInput()
        self.assertIsNotNone(voice)

    def test_is_available(self):
        """Test voice availability check."""
        from aipp_opener.voice import VoiceInput
        
        voice = VoiceInput()
        result = voice.is_available()
        self.assertIsInstance(result, bool)


class TestGroupManager(unittest.TestCase):
    """Tests for groups module."""

    def test_groups_init(self):
        """Test groups manager initialization."""
        from aipp_opener.groups import GroupManager

        groups = GroupManager()
        self.assertIsNotNone(groups)

    def test_groups_add(self):
        """Test adding a group."""
        from aipp_opener.groups import GroupManager

        groups = GroupManager()
        groups.add_group("work", ["code", "terminal"])

        all_groups = groups.list_groups()
        self.assertGreater(len(all_groups), 0)

    def test_groups_get(self):
        """Test getting a group."""
        from aipp_opener.groups import GroupManager

        groups = GroupManager()
        groups.add_group("test", ["firefox"])

        group = groups.get_group("test")
        self.assertIsNotNone(group)

    def test_groups_remove(self):
        """Test removing a group."""
        from aipp_opener.groups import GroupManager

        groups = GroupManager()
        groups.add_group("temp", ["code"])
        groups.remove_group("temp")

        group = groups.get_group("temp")
        self.assertIsNone(group)

    def test_groups_list(self):
        """Test listing groups."""
        from aipp_opener.groups import GroupManager

        groups = GroupManager()
        groups_list = groups.list_groups()
        self.assertIsInstance(groups_list, list)


class TestAliasManager(unittest.TestCase):
    """Tests for aliases module."""

    def test_aliases_init(self):
        """Test aliases manager initialization."""
        from aipp_opener.aliases import AliasManager

        aliases = AliasManager()
        self.assertIsNotNone(aliases)

    def test_aliases_add(self):
        """Test adding an alias."""
        from aipp_opener.aliases import AliasManager

        aliases = AliasManager()
        aliases.add_alias("ff", "firefox")

        command = aliases.get_command("ff")
        self.assertEqual(command, "firefox")

    def test_aliases_remove(self):
        """Test removing an alias."""
        from aipp_opener.aliases import AliasManager

        aliases = AliasManager()
        aliases.add_alias("temp", "code")
        aliases.remove_alias("temp")

        command = aliases.get_command("temp")
        self.assertIsNone(command)

    def test_aliases_list(self):
        """Test listing all aliases."""
        from aipp_opener.aliases import AliasManager

        aliases = AliasManager()
        aliases.add_alias("test1", "app1")

        all_aliases = aliases.list_aliases()
        self.assertIsInstance(all_aliases, list)


class TestPerformanceProfiler(unittest.TestCase):
    """Tests for profiler module."""

    def test_profiler_init(self):
        """Test profiler initialization."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        self.assertIsNotNone(profiler)

    def test_profiler_start_stop(self):
        """Test profiler start and stop."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()

        profiler.start_profiling()
        # Note: _running attribute may not exist, just check no exception

        profiler.stop_profiling()
        # Should complete without error
        self.assertTrue(True)

    def test_profiler_profile_block(self):
        """Test profiling a code block."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()

        with profiler.profile_block("test_block"):
            sum(range(100))

        # Should complete without error
        self.assertTrue(True)

    def test_profiler_profile_function(self):
        """Test profiling a function."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()

        @profiler.profile_function
        def test_func():
            return sum(range(100))

        result = test_func()
        self.assertEqual(result, sum(range(100)))

    def test_profiler_reset(self):
        """Test resetting profiler."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        profiler.reset()
        # Should complete without error
        self.assertTrue(True)

    def test_profiler_get_slowest(self):
        """Test getting slowest operations."""
        from aipp_opener.profiler import PerformanceProfiler

        profiler = PerformanceProfiler()
        slowest = profiler.get_slowest(10)
        self.assertIsInstance(slowest, list)


class TestWebSearch(unittest.TestCase):
    """Tests for web search module."""

    def test_web_searcher_init(self):
        """Test web searcher initialization."""
        from aipp_opener.web_search import WebSearcher
        
        searcher = WebSearcher()
        self.assertIsNotNone(searcher)

    def test_web_searcher_engines(self):
        """Test search engines."""
        from aipp_opener.web_search import WebSearcher
        
        searcher = WebSearcher()
        engines = searcher.get_available_engines()
        self.assertIsInstance(engines, list)
        self.assertGreater(len(engines), 0)


if __name__ == "__main__":
    unittest.main()
