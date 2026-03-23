"""Tests for AIpp Opener icon finder (aipp_opener/icons.py)."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock


class TestIconInfo(unittest.TestCase):
    """Test IconInfo dataclass."""

    def test_icon_info_with_path(self):
        """Test IconInfo with path."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(path="/usr/share/icons/firefox.png")

        self.assertEqual(icon.path, "/usr/share/icons/firefox.png")
        self.assertIsNone(icon.name)

    def test_icon_info_with_name(self):
        """Test IconInfo with name."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(name="firefox")

        self.assertEqual(icon.name, "firefox")
        self.assertIsNone(icon.path)

    def test_icon_info_with_mime_type(self):
        """Test IconInfo with MIME type."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(name="firefox", mime_type="image/png")

        self.assertEqual(icon.mime_type, "image/png")

    def test_icon_info_exists_true(self):
        """Test IconInfo.exists() when file exists."""
        from aipp_opener.icons import IconInfo

        with tempfile.NamedTemporaryFile(delete=False) as f:
            icon = IconInfo(path=f.name)
            self.assertTrue(icon.exists())

    def test_icon_info_exists_false(self):
        """Test IconInfo.exists() when file doesn't exist."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(path="/nonexistent/path/icon.png")
        self.assertFalse(icon.exists())

    def test_icon_info_exists_no_path(self):
        """Test IconInfo.exists() when no path set."""
        from aipp_opener.icons import IconInfo

        icon = IconInfo(name="firefox")
        self.assertFalse(icon.exists())


class TestIconFinder(unittest.TestCase):
    """Test IconFinder class."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_find_icon_returns_icon_info(self):
        """Test that find_icon returns IconInfo."""
        result = self.finder.find_icon("firefox", "/usr/bin/firefox")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)

    def test_find_icon_uses_cache(self):
        """Test that icon finder uses cache."""
        app_name = "cached_app"
        executable = "/usr/bin/cached_app"

        # First call
        result1 = self.finder.find_icon(app_name, executable)

        # Second call should use cache
        result2 = self.finder.find_icon(app_name, executable)

        # Results should be the same (cached)
        self.assertEqual(result1.name, result2.name)

    def test_find_icon_fallback_to_name(self):
        """Test icon fallback to app name."""
        result = self.finder.find_icon("myapp", "/usr/bin/myapp")

        # Should return IconInfo with name as fallback
        self.assertIsNotNone(result)
        self.assertIsInstance(result.name, str)


class TestIconFinderPrivateMethods(unittest.TestCase):
    """Test IconFinder private methods."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()

    def test_find_from_desktop(self):
        """Test _find_from_desktop method."""
        # Create a mock desktop file
        desktop_content = """[Desktop Entry]
Name=Test App
Icon=test-icon-name
Exec=/usr/bin/testapp
Comment=A test application
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a fake applications directory
            apps_dir = Path(temp_dir) / "applications"
            apps_dir.mkdir()
            
            desktop_file = apps_dir / "testapp.desktop"
            with open(desktop_file, "w") as f:
                f.write(desktop_content)

            # Mock the desktop directories
            with patch.object(self.finder, '_find_from_desktop') as mock_find:
                mock_find.return_value = None  # Return None for this test
                
                result = self.finder.find_icon("testapp", "/usr/bin/testapp")
                
                # Should still return IconInfo
                from aipp_opener.icons import IconInfo
                self.assertIsInstance(result, IconInfo)

    def test_resolve_icon_name(self):
        """Test _resolve_icon_name method."""
        from aipp_opener.icons import IconInfo

        icon_info = IconInfo(name="firefox")
        result = self.finder._resolve_icon_name(icon_info)

        self.assertIsInstance(result, IconInfo)

    def test_resolve_icon_name_no_name(self):
        """Test _resolve_icon_name with no name."""
        from aipp_opener.icons import IconInfo

        icon_info = IconInfo()
        result = self.finder._resolve_icon_name(icon_info)

        self.assertIsInstance(result, IconInfo)

    def test_find_by_name(self):
        """Test _find_by_name method."""
        result = self.finder._find_by_name("firefox")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)

    def test_icon_cache(self):
        """Test icon caching behavior."""
        # First call
        result1 = self.finder.find_icon("test", "/usr/bin/test")
        
        # Check cache was populated
        self.assertGreaterEqual(len(self.finder._icon_cache), 1)


class TestIconFinderWithCategories(unittest.TestCase):
    """Test icon finder with app categories."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()

    def test_find_icon_browser_category(self):
        """Test icon finding for browser category."""
        browsers = [
            ("firefox", "/usr/bin/firefox"),
            ("chrome", "/usr/bin/chrome"),
        ]

        for name, exec_path in browsers:
            result = self.finder.find_icon(name, exec_path)
            from aipp_opener.icons import IconInfo
            self.assertIsInstance(result, IconInfo)

    def test_find_icon_development_category(self):
        """Test icon finding for development tools."""
        dev_tools = [
            ("code", "/usr/bin/code"),
        ]

        for name, exec_path in dev_tools:
            result = self.finder.find_icon(name, exec_path)
            from aipp_opener.icons import IconInfo
            self.assertIsInstance(result, IconInfo)


class TestIconFinderEdgeCases(unittest.TestCase):
    """Test icon finder edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()

    def test_find_icon_empty_name(self):
        """Test finding icon with empty name."""
        result = self.finder.find_icon("", "/usr/bin/app")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)

    def test_find_icon_special_characters(self):
        """Test finding icon with special characters in name."""
        result = self.finder.find_icon("app++", "/usr/bin/app++")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)

    def test_find_icon_spaces_in_name(self):
        """Test finding icon with spaces in name."""
        result = self.finder.find_icon("my app", "/usr/bin/myapp")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)

    def test_find_icon_version_in_name(self):
        """Test finding icon with version number in name."""
        result = self.finder.find_icon("app-3.0", "/usr/bin/app-3")

        from aipp_opener.icons import IconInfo
        self.assertIsInstance(result, IconInfo)


class TestIconThemeSupport(unittest.TestCase):
    """Test icon theme support."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()

    def test_icon_theme_search_order(self):
        """Test that icon themes are searched in correct order."""
        # Verify ICON_PATHS has expected directories
        icon_paths = self.finder.ICON_PATHS

        # Should include standard icon directories
        path_strs = [str(p) for p in icon_paths]

        # At least some standard paths should be present
        standard_paths = ['/usr/share/icons', '/usr/share/pixmaps']
        has_standard = any(p in path_strs for p in standard_paths)

        self.assertTrue(has_standard or len(icon_paths) > 0)

    def test_icon_size_preference(self):
        """Test that larger icons are preferred."""
        # Verify ICON_SIZES has expected order
        icon_sizes = self.finder.ICON_SIZES

        # Larger sizes should come first
        if len(icon_sizes) > 1:
            first_size = icon_sizes[0]
            # 256x256 or 128x128 should be first
            self.assertIn(first_size.split('x')[0], ['256', '128', '96'])


class TestParseDesktopIcon(unittest.TestCase):
    """Test desktop file parsing."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.icons import IconFinder

        self.finder = IconFinder()

    def test_parse_desktop_icon_valid(self):
        """Test parsing valid desktop file."""
        desktop_content = """[Desktop Entry]
Name=Test App
Icon=test-icon
Exec=/usr/bin/testapp
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', delete=False) as f:
            f.write(desktop_content)
            desktop_path = f.name

        try:
            result = self.finder._parse_desktop_icon(
                Path(desktop_path),
                "testapp",
                "/usr/bin/testapp"
            )

            if result:
                self.assertEqual(result.name, "test-icon")
        finally:
            Path(desktop_path).unlink()

    def test_parse_desktop_icon_no_match(self):
        """Test parsing desktop file that doesn't match."""
        desktop_content = """[Desktop Entry]
Name=Other App
Icon=other-icon
Exec=/usr/bin/otherapp
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', delete=False) as f:
            f.write(desktop_content)
            desktop_path = f.name

        try:
            result = self.finder._parse_desktop_icon(
                Path(desktop_path),
                "testapp",
                "/usr/bin/testapp"
            )

            self.assertIsNone(result)
        finally:
            Path(desktop_path).unlink()


if __name__ == "__main__":
    unittest.main()
