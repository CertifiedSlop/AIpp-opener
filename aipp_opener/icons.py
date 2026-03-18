"""App icon support for AIpp Opener."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class IconInfo:
    """Icon information for an application."""

    path: Optional[str] = None
    name: Optional[str] = None
    mime_type: Optional[str] = None

    def exists(self) -> bool:
        """Check if icon exists."""
        if self.path:
            return Path(self.path).exists()
        return False


class IconFinder:
    """Finds icons for applications."""

    # Common icon themes and their paths
    ICON_PATHS = [
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps"),
        Path.home() / ".icons",
        Path.home() / ".local" / "share" / "icons",
        Path("/run/current-system/sw/share/icons"),
    ]

    # Icon sizes to search (prefer larger icons)
    ICON_SIZES = ["256x256", "128x128", "96x96", "64x64", "48x48", "32x32", "24x24", "scalable"]

    def __init__(self):
        self._icon_cache: dict[str, IconInfo] = {}

    def find_icon(self, app_name: str, app_executable: str) -> IconInfo:
        """
        Find icon for an application.

        Args:
            app_name: Application name.
            app_executable: Application executable.

        Returns:
            IconInfo with icon details.
        """
        cache_key = f"{app_name}:{app_executable}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        icon = self._find_icon_slow(app_name, app_executable)
        self._icon_cache[cache_key] = icon
        return icon

    def _find_icon_slow(self, app_name: str, app_executable: str) -> IconInfo:
        """Actually find the icon (not cached)."""
        # Try to find from desktop file
        desktop_icon = self._find_from_desktop(app_name, app_executable)
        if desktop_icon and desktop_icon.exists():
            return desktop_icon

        # Try common icon names
        for name in [app_name.lower(), app_executable.lower()]:
            icon = self._find_by_name(name)
            if icon and icon.exists():
                return icon

        # Try without special characters
        clean_name = app_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        icon = self._find_by_name(clean_name)
        if icon and icon.exists():
            return icon

        # Return default icon info
        return IconInfo(name="application-x-executable")

    def _find_from_desktop(self, app_name: str, app_executable: str) -> IconInfo:
        """Find icon from desktop file."""
        desktop_dirs = [
            Path("/usr/share/applications"),
            Path.home() / ".local" / "share" / "applications",
            Path("/run/current-system/sw/share/applications"),
        ]

        for desktop_dir in desktop_dirs:
            if not desktop_dir.exists():
                continue

            for desktop_file in desktop_dir.glob("*.desktop"):
                try:
                    info = self._parse_desktop_icon(desktop_file, app_name, app_executable)
                    if info:
                        # Try to resolve the icon
                        return self._resolve_icon_name(info)
                except Exception:
                    continue

        return IconInfo()

    def _parse_desktop_icon(
        self, desktop_file: Path, app_name: str, app_executable: str
    ) -> Optional[IconInfo]:
        """Parse desktop file for icon information."""
        try:
            with open(desktop_file, "r", encoding="utf-8", errors="ignore") as f:
                in_desktop_entry = False
                icon_value = None
                exec_value = None

                for line in f:
                    line = line.strip()
                    if line == "[Desktop Entry]":
                        in_desktop_entry = True
                        continue
                    elif line.startswith("[") and in_desktop_entry:
                        break

                    if in_desktop_entry:
                        if line.startswith("Icon="):
                            icon_value = line.split("=", 1)[1].strip()
                        elif line.startswith("Exec="):
                            exec_value = line.split("=", 1)[1].strip()

                # Check if this desktop file matches
                if exec_value:
                    exec_name = exec_value.split()[0] if exec_value else ""
                    if exec_name and (
                        app_name.lower() == exec_name.lower() or app_executable.endswith(exec_name)
                    ):
                        if icon_value:
                            return IconInfo(name=icon_value)
        except Exception:
            pass

        return None

    def _resolve_icon_name(self, icon_info: IconInfo) -> IconInfo:
        """Resolve icon name to actual path."""
        if not icon_info.name:
            return icon_info

        name = icon_info.name

        # If it's an absolute path
        if name.startswith("/"):
            icon_info.path = name
            return icon_info

        # Search in icon paths
        for icon_path in self.ICON_PATHS:
            if not icon_path.exists():
                continue

            # Try different extensions
            for ext in [".png", ".svg", ".xpm"]:
                # Direct in pixmaps
                direct_path = icon_path / f"{name}{ext}"
                if direct_path.exists():
                    icon_info.path = str(direct_path)
                    icon_info.mime_type = self._get_mime_type(ext)
                    return icon_info

                # Search in themed icons
                for size in self.ICON_SIZES:
                    if size == "scalable":
                        themed_path = icon_path / "hicolor" / "scalable" / "apps" / f"{name}{ext}"
                    else:
                        themed_path = icon_path / "hicolor" / size / "apps" / f"{name}{ext}"

                    if themed_path.exists():
                        icon_info.path = str(themed_path)
                        icon_info.mime_type = self._get_mime_type(ext)
                        return icon_info

        return icon_info

    def _find_by_name(self, name: str) -> IconInfo:
        """Find icon by name."""
        for icon_path in self.ICON_PATHS:
            if not icon_path.exists():
                continue

            for ext in [".png", ".svg", ".xpm"]:
                # Check pixmaps
                direct = icon_path / f"{name}{ext}"
                if direct.exists():
                    return IconInfo(path=str(direct), name=name, mime_type=self._get_mime_type(ext))

                # Check themed
                for size in self.ICON_SIZES:
                    if size == "scalable":
                        themed = icon_path / "hicolor" / "scalable" / "apps" / f"{name}{ext}"
                    else:
                        themed = icon_path / "hicolor" / size / "apps" / f"{name}{ext}"

                    if themed.exists():
                        return IconInfo(
                            path=str(themed), name=name, mime_type=self._get_mime_type(ext)
                        )

        return IconInfo(name=name)

    def _get_mime_type(self, ext: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".xpm": "image/x-xpixmap",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mime_types.get(ext, "application/octet-stream")

    def get_icon_base64(self, icon_info: IconInfo) -> Optional[str]:
        """
        Get icon as base64 encoded string.

        Args:
            icon_info: Icon information.

        Returns:
            Base64 encoded icon or None.
        """
        if not icon_info.path or not Path(icon_info.path).exists():
            return None

        try:
            import base64

            with open(icon_info.path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None

    def get_fallback_icon(self) -> str:
        """Get path to fallback icon."""
        # Try to find a generic application icon
        for icon_path in self.ICON_PATHS:
            for name in ["application-x-executable", "system-run", "utilities-terminal"]:
                for ext in [".png", ".svg"]:
                    path = icon_path / "hicolor" / "48x48" / "apps" / f"{name}{ext}"
                    if path.exists():
                        return str(path)

                    path = icon_path / f"{name}{ext}"
                    if path.exists():
                        return str(path)

        return ""
