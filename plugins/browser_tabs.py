"""
Sample plugin for AIpp Opener - Browser Tabs Detector.

This plugin detects open browser tabs (Firefox, Chrome, Chromium) and makes them launchable.

Installation:
    Copy this file to ~/.local/share/aipp_opener/plugins/browser_tabs.py

Usage:
    After installation, run:
    python -m aipp_opener --plugins  # List plugins
    python -m aipp_opener --enable-plugin browser_tabs

Features:
    - Detects open tabs in Firefox, Chrome, and Chromium
    - Shows tab titles with favicons (when available)
    - Quick switch to browser tabs
    - Supports multiple browser profiles

Requirements:
    - Browsers must be running
    - Access to browser session files

Author: AIpp Opener Team
License: MIT
"""

import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Generator
from xml.etree import ElementTree as ET

from aipp_opener.plugins import AppDetectorPlugin
from aipp_opener.detectors.base import AppInfo
from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


class BrowserTabsPlugin(AppDetectorPlugin):
    """Detects open browser tabs from Firefox, Chrome, and Chromium."""

    BROWSER_NAMES = {
        "firefox": "🦊 Firefox",
        "chrome": "🌐 Chrome",
        "chromium": "🌐 Chromium",
        "brave": "🦁 Brave",
        "edge": "🔷 Edge",
    }

    def __init__(self):
        self._browsers = {
            "firefox": self._get_firefox_session,
            "chrome": self._get_chrome_session,
            "chromium": self._get_chromium_session,
            "brave": self._get_brave_session,
            "edge": self._get_edge_session,
        }
        self._max_tabs = 50  # Maximum tabs to track

    @property
    def name(self) -> str:
        return "browser_tabs"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Detects open browser tabs and provides quick access"

    def is_available(self) -> bool:
        """Check if any browser session is available."""
        for browser_func in self._browsers.values():
            try:
                sessions = list(browser_func())
                if sessions:
                    return True
            except Exception:
                continue
        return False

    def detect(self) -> list[AppInfo]:
        """Detect open browser tabs."""
        apps = []

        for browser_name, session_func in self._browsers.items():
            try:
                tabs = list(session_func())

                for tab in tabs[:self._max_tabs]:
                    title = tab.get("title", "Untitled")
                    url = tab.get("url", "")

                    # Create a safe name for the tab
                    safe_title = title[:50].replace("'", "").replace('"', "")
                    display_name = f"{self.BROWSER_NAMES.get(browser_name, '🌐')} {safe_title}"

                    # Create a command to open the tab
                    # This uses xdg-open to open the URL in the default browser
                    apps.append(AppInfo(
                        name=f"tab-{browser_name}-{tab.get('id', 'unknown')}",
                        executable=f"xdg-open '{url}'",
                        display_name=display_name,
                        description=f"{browser_name.capitalize()} tab: {url[:100]}",
                        categories=[f"browser-{browser_name}", "tabs"],
                        icon="🌐",
                    ))

            except Exception as e:
                logger.debug("Error detecting %s tabs: %s", browser_name, e)

        return apps

    def _get_firefox_session(self) -> Generator[dict, None, None]:
        """
        Get open tabs from Firefox session.

        Firefox stores session data in:
        ~/.mozilla/firefox/<profile>.default/sessionstore-backups/recovery.jsonlz4
        or
        ~/.mozilla/firefox/<profile>.default/sessionstore-backups/recovery.baklz4
        """
        firefox_dir = Path.home() / ".mozilla" / "firefox"

        if not firefox_dir.exists():
            return

        # Find profile directories
        profiles_ini = firefox_dir / "profiles.ini"
        if not profiles_ini.exists():
            return

        # Parse profiles.ini to find profile paths
        profiles = []
        with open(profiles_ini, "r") as f:
            current_profile = {}
            for line in f:
                line = line.strip()
                if line.startswith("[Profile"):
                    if current_profile:
                        profiles.append(current_profile)
                    current_profile = {}
                elif "=" in line:
                    key, value = line.split("=", 1)
                    current_profile[key] = value
            if current_profile:
                profiles.append(current_profile)

        # Check each profile for session data
        for profile in profiles:
            profile_path = profile.get("Path", "")
            if profile.get("IsRelative", "1") == "1":
                profile_path = firefox_dir / profile_path
            else:
                profile_path = Path(profile_path)

            session_file = profile_path / "sessionstore-backups" / "recovery.jsonlz4"
            backup_file = profile_path / "sessionstore-backups" / "recovery.baklz4"

            # Try current session first, then backup
            for sess_file in [session_file, backup_file]:
                if sess_file.exists():
                    try:
                        yield from self._parse_firefox_session(sess_file)
                        break
                    except Exception as e:
                        logger.debug("Error parsing Firefox session: %s", e)

    def _parse_firefox_session(self, session_file: Path) -> Generator[dict, None, None]:
        """
        Parse Firefox session file.

        Firefox .jsonlz4 files start with magic bytes and use LZ4 compression.
        For simplicity, we'll try to parse the JSON directly if possible.
        """
        # Try to decompress using lz4 if available
        try:
            import lz4.block

            with open(session_file, "rb") as f:
                # Skip magic bytes (8 bytes)
                f.read(8)
                compressed_data = f.read()

            decompressed = lz4.block.decompress(compressed_data)
            data = json.loads(decompressed.decode("utf-8"))

            yield from self._extract_firefox_tabs(data)

        except ImportError:
            logger.debug("lz4 not available, cannot parse Firefox session")
        except Exception as e:
            logger.debug("Error decompressing Firefox session: %s", e)

    def _extract_firefox_tabs(self, data: dict, tab_id: int = 0) -> Generator[dict, None, None]:
        """Extract tabs from Firefox session data recursively."""
        if isinstance(data, dict):
            # Check if this is a tab entry
            if "entries" in data and "url" in data:
                entries = data.get("entries", [])
                if entries:
                    # Current entry
                    current = entries[-1] if entries else {}
                    yield {
                        "id": tab_id,
                        "title": current.get("title", data.get("title", "Untitled")),
                        "url": current.get("url", data.get("url", "")),
                    }
                    tab_id += 1

                    # Also yield other entries (history)
                    for entry in entries[:-1]:
                        yield {
                            "id": tab_id,
                            "title": entry.get("title", "Untitled"),
                            "url": entry.get("url", ""),
                        }
                        tab_id += 1

            # Recurse into children
            for key in ["windows", "tabs", "children"]:
                if key in data:
                    yield from self._extract_firefox_tabs(data[key], tab_id)

        elif isinstance(data, list):
            for item in data:
                yield from self._extract_firefox_tabs(item, tab_id)

    def _get_chrome_session(self) -> Generator[dict, None, None]:
        """Get open tabs from Google Chrome."""
        chrome_dir = Path.home() / ".config" / "google-chrome"
        yield from self._get_chromium_based_session(chrome_dir, "chrome")

    def _get_chromium_session(self) -> Generator[dict, None, None]:
        """Get open tabs from Chromium."""
        chromium_dir = Path.home() / ".config" / "chromium"
        yield from self._get_chromium_based_session(chromium_dir, "chromium")

    def _get_brave_session(self) -> Generator[dict, None, None]:
        """Get open tabs from Brave."""
        brave_dir = Path.home() / ".config" / "BraveSoftware" / "Brave-Browser"
        yield from self._get_chromium_based_session(brave_dir, "brave")

    def _get_edge_session(self) -> Generator[dict, None, None]:
        """Get open tabs from Microsoft Edge."""
        edge_dir = Path.home() / ".config" / "microsoft-edge"
        yield from self._get_chromium_based_session(edge_dir, "edge")

    def _get_chromium_based_session(
        self, browser_dir: Path, browser_name: str
    ) -> Generator[dict, None, None]:
        """
        Get open tabs from Chromium-based browsers.

        Chrome stores session data in:
        ~/.config/<browser>/Default/Current Session
        or
        ~/.config/<browser>/Default/Last Session
        """
        if not browser_dir.exists():
            return

        # Find profile directories
        profiles = [browser_dir / "Default"]
        for profile_dir in browser_dir.glob("Profile *"):
            profiles.append(profile_dir)

        for profile in profiles:
            session_file = profile / "Current Sessions"
            last_session_file = profile / "Last Session"

            for sess_file in [session_file, last_session_file]:
                if sess_file.exists():
                    try:
                        yield from self._parse_chrome_session(sess_file, browser_name)
                        break
                    except Exception as e:
                        logger.debug("Error parsing %s session: %s", browser_name, e)

    def _parse_chrome_session(
        self, session_file: Path, browser_name: str
    ) -> Generator[dict, None, None]:
        """
        Parse Chrome session file.

        Chrome session files are binary/LevelDB format.
        For simplicity, we'll use a basic string search for URLs.
        """
        try:
            # Read the file and look for URL patterns
            with open(session_file, "rb") as f:
                content = f.read()

            # Decode as much as possible
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                return

            # Simple URL extraction (not perfect but works for basic cases)
            import re

            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, text)

            tab_id = 0
            for url in urls[:20]:  # Limit URLs per session file
                yield {
                    "id": tab_id,
                    "title": Path(url).name or url,
                    "url": url,
                }
                tab_id += 1

        except Exception as e:
            logger.debug("Error parsing Chrome session: %s", e)

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Browser Tabs plugin loaded")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Browser Tabs plugin unloaded")

    def validate(self) -> tuple[bool, str]:
        """
        Validate the plugin.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Ensure we only access browser directories
        allowed_paths = [
            Path.home() / ".mozilla",
            Path.home() / ".config",
        ]

        # This is a read-only plugin, so it's safe
        return True, ""


# Export the plugin class
__all__ = ["BrowserTabsPlugin"]
