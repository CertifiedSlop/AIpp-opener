"""
Sample plugin for AIpp Opener - Recent Files Detector.

This plugin detects recently opened files and makes them quickly accessible.

Installation:
    Copy this file to ~/.local/share/aipp_opener/plugins/recent_files.py

Usage:
    After installation, run:
    python -m aipp_opener --plugins  # List plugins
    python -m aipp_opener --enable-plugin recent_files

Features:
    - Detects recently opened files from GTK recent documents
    - Shows files categorized by type (documents, images, code, etc.)
    - Quick launch for recent files with their default applications

Author: AIpp Opener Team
License: MIT
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from aipp_opener.plugins import AppDetectorPlugin
from aipp_opener.detectors.base import AppInfo
from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


class RecentFilesPlugin(AppDetectorPlugin):
    """Detects recently opened files from GTK recent documents."""

    # File type categories with emojis
    FILE_CATEGORIES = {
        "document": ["pdf", "doc", "docx", "odt", "txt", "md", "rst"],
        "spreadsheet": ["xls", "xlsx", "ods", "csv"],
        "presentation": ["ppt", "pptx", "odp"],
        "image": ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp"],
        "code": ["py", "js", "ts", "java", "c", "cpp", "h", "hpp", "rs", "go", "sh"],
        "archive": ["zip", "tar", "gz", "rar", "7z"],
        "video": ["mp4", "avi", "mkv", "webm", "mov"],
        "audio": ["mp3", "wav", "flac", "ogg", "m4a"],
    }

    FILE_EMOJIS = {
        "document": "📄",
        "spreadsheet": "📊",
        "presentation": "📽️",
        "image": "🖼️",
        "code": "💻",
        "archive": "📦",
        "video": "🎬",
        "audio": "🎵",
        "unknown": "📁",
    }

    def __init__(self):
        self._recent_file = Path.home() / ".local" / "share" / "recently-used.xbel"
        self._max_recent = 20  # Maximum recent files to track

    @property
    def name(self) -> str:
        return "recent_files"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Detects recently opened files and provides quick access"

    def is_available(self) -> bool:
        """Check if recent files are available."""
        return self._recent_file.exists()

    def detect(self) -> list[AppInfo]:
        """Detect recently opened files."""
        apps = []

        if not self.is_available():
            logger.debug("Recent files not available: %s not found", self._recent_file)
            return apps

        try:
            recent_files = self._parse_recent_files()

            for file_info in recent_files[:self._max_recent]:
                file_path = file_info["path"]
                category = self._categorize_file(file_path)
                emoji = self.FILE_EMOJIS.get(category, self.FILE_EMOJIS["unknown"])

                # Create a launcher for the file
                display_name = f"{emoji} {Path(file_path).name}"
                description = f"Recent {category} file - {file_info.get('modified', 'Unknown time')}"

                # Use xdg-open to open the file with its default application
                apps.append(AppInfo(
                    name=f"recent-{Path(file_path).stem}",
                    executable=f"xdg-open '{file_path}'",
                    display_name=display_name,
                    description=description,
                    categories=[f"recent-{category}"],
                    icon=self.FILE_EMOJIS.get(category, "📁"),
                ))

        except Exception as e:
            logger.error("Error detecting recent files: %s", e)

        return apps

    def _parse_recent_files(self) -> list[dict]:
        """
        Parse GTK recent documents file.

        Returns:
            List of recent file information dictionaries.
        """
        recent_files = []

        try:
            tree = ET.parse(self._recent_file)
            root = tree.getroot()

            # XBEL namespace
            ns = {"xbel": "http://www.freedesktop.org/standards/shared-mime-info/xbel"}

            for bookmark in root.findall("bookmark"):
                try:
                    href = bookmark.get("href", "")
                    if not href or href.startswith("file://"):
                        # Decode file:// URL
                        file_path = unquote(href[7:])  # Remove file://

                        # Check if file still exists
                        if not os.path.exists(file_path):
                            continue

                        # Get metadata
                        info = {
                            "path": file_path,
                            "modified": "Unknown",
                            "visited": "Unknown",
                        }

                        # Try to get modification time
                        mtime_info = bookmark.find(".//{http://www.freedesktop.org/standards/shared-mime-info/xbel}mtime")
                        if mtime_info is not None and mtime_info.text:
                            try:
                                timestamp = float(mtime_info.text)
                                info["modified"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                            except (ValueError, OSError):
                                pass

                        # Try to get visit time
                        visited_info = bookmark.find(".//{http://www.freedesktop.org/standards/shared-mime-info/xbel}visited")
                        if visited_info is not None and visited_info.text:
                            try:
                                timestamp = float(visited_info.text)
                                info["visited"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                            except (ValueError, OSError):
                                pass

                        recent_files.append(info)

                except Exception as e:
                    logger.debug("Error parsing bookmark: %s", e)
                    continue

        except ET.ParseError as e:
            logger.warning("Could not parse recent files: %s", e)

        # Sort by modification time (most recent first)
        recent_files.sort(
            key=lambda x: x.get("modified", ""),
            reverse=True
        )

        return recent_files

    def _categorize_file(self, file_path: str) -> str:
        """
        Categorize a file by its extension.

        Args:
            file_path: Path to the file.

        Returns:
            Category name.
        """
        ext = Path(file_path).suffix.lower().lstrip(".")

        for category, extensions in self.FILE_CATEGORIES.items():
            if ext in extensions:
                return category

        return "unknown"

    def get_recent_files(self, limit: int = 10, category: Optional[str] = None) -> list[dict]:
        """
        Get recent files with optional filtering.

        Args:
            limit: Maximum number of files to return.
            category: Optional category filter.

        Returns:
            List of recent file information.
        """
        files = self._parse_recent_files()

        if category:
            files = [f for f in files if self._categorize_file(f["path"]) == category]

        return files[:limit]

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Recent Files plugin loaded")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Recent Files plugin unloaded")

    def validate(self) -> tuple[bool, str]:
        """
        Validate the plugin.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check that we're not accessing sensitive directories
        home = str(Path.home())
        if not home.startswith("/home/"):
            return False, "Plugin should only access user home directory"

        return True, ""


# Export the plugin class
__all__ = ["RecentFilesPlugin"]
