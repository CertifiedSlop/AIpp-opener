"""Fedora-specific application detector."""

import subprocess
import os
from pathlib import Path
from typing import Optional

from aipp_opener.detectors.base import AppDetector, AppInfo
from aipp_opener.categories import AppCategorizer, AppCategory
from aipp_opener.cache import AppDetectionCache
from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


class FedoraAppDetector(AppDetector):
    """Detects applications installed on Fedora/RHEL systems."""

    def __init__(self):
        self._cache: Optional[list[AppInfo]] = None
        self.categorizer = AppCategorizer()
        self.app_cache = AppDetectionCache(ttl=600)  # 10 minute cache

    def is_available(self) -> bool:
        """Check if running on a Fedora-based system."""
        # Check for Fedora/RHEL-specific files
        return (
            Path("/etc/fedora-release").exists()
            or Path("/etc/redhat-release").exists()
            or self._rpm_available()
        )

    def _rpm_available(self) -> bool:
        """Check if rpm command is available."""
        try:
            result = subprocess.run(
                ["rpm", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def detect(self) -> list[AppInfo]:
        """Detect installed applications on Fedora systems."""
        # Check memory cache first
        if self._cache is not None:
            return self._cache

        # Check disk cache
        cached_apps = self.app_cache.get_apps("fedora")
        if cached_apps is not None:
            logger.debug("Using cached app detection results for Fedora")
            return [AppInfo(**app) for app in cached_apps]

        apps = []
        seen_executables = set()

        # Method 1: Query rpm/dnf for installed packages
        apps.extend(self._detect_from_rpm())

        # Method 2: Scan desktop files for GUI apps
        apps.extend(self._detect_from_desktop_files())

        # Method 3: Scan common binary paths
        apps.extend(self._detect_from_bin_paths())

        # Deduplicate by executable
        unique_apps = []
        for app in apps:
            if app.executable not in seen_executables:
                seen_executables.add(app.executable)
                unique_apps.append(app)

        # Cache the results
        self._cache = unique_apps
        self.app_cache.set_apps("fedora", [app.__dict__ for app in unique_apps])

        return unique_apps

    def _detect_from_rpm(self) -> list[AppInfo]:
        """Detect apps from rpm package database."""
        apps = []

        try:
            # Query all installed packages
            result = subprocess.run(
                ["rpm", "-qa", "--qf", "%{NAME}\n"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                packages = result.stdout.strip().split("\n")

                # Get files for each package (limited to avoid timeout)
                for pkg in packages[:500]:  # Limit to first 500 packages
                    pkg_apps = self._get_package_executables(pkg)
                    for exec_name in pkg_apps:
                        if exec_name not in [a.executable for a in apps]:
                            category = self.categorizer.get_category(exec_name)
                            apps.append(
                                AppInfo(
                                    name=pkg,
                                    executable=exec_name,
                                    display_name=self._format_name(pkg),
                                    categories=[category.value] if category else [],
                                )
                            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.warning("Error querying rpm: %s", e)

        return apps

    def _get_package_executables(self, package: str) -> list[str]:
        """Get executables provided by a package."""
        executables = []

        try:
            result = subprocess.run(
                ["rpm", "-ql", package],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                files = result.stdout.strip().split("\n")
                for file_path in files:
                    # Check if it's an executable in a bin directory
                    if any(
                        bin_dir in file_path
                        for bin_dir in ["/bin/", "/sbin/", "/usr/bin/", "/usr/sbin/"]
                    ):
                        exec_name = os.path.basename(file_path)
                        # Filter out common non-app executables
                        if not exec_name.startswith(".") and exec_name not in [
                            "sh",
                            "bash",
                            "ldconfig",
                            "ld.so",
                        ]:
                            executables.append(exec_name)
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            pass

        return executables[:10]  # Limit executables per package

    def _detect_from_desktop_files(self) -> list[AppInfo]:
        """Detect GUI applications from .desktop files."""
        apps = []
        desktop_dirs = [
            Path("/usr/share/applications"),
            Path.home() / ".local" / "share" / "applications",
        ]

        for desktop_dir in desktop_dirs:
            if not desktop_dir.exists():
                continue

            for desktop_file in desktop_dir.glob("*.desktop"):
                try:
                    info = self._parse_desktop_file(desktop_file)
                    if info and info.get("Exec"):
                        exec_name = info["Exec"].split()[0]
                        name = info.get("Name", exec_name)

                        # Check if executable exists
                        if self._executable_exists(exec_name):
                            categories = info.get("Categories", [])
                            if isinstance(categories, str):
                                categories = categories.split(";")

                            apps.append(
                                AppInfo(
                                    name=name.lower().replace(" ", "-"),
                                    executable=exec_name,
                                    display_name=name,
                                    description=info.get("Comment", ""),
                                    categories=categories,
                                )
                            )
                except Exception as e:
                    logger.debug("Error parsing desktop file %s: %s", desktop_file, e)

        return apps

    def _detect_from_bin_paths(self) -> list[AppInfo]:
        """Scan common binary paths for executables."""
        apps = []
        bin_paths = [
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/bin"),
            Path("/usr/sbin"),
            Path("/usr/local/sbin"),
            Path("/sbin"),
            Path.home() / ".local" / "bin",
        ]

        common_gui_apps = [
            "firefox",
            "chrome",
            "chromium",
            "code",
            "libreoffice",
            "gedit",
            "nautilus",
            "thunderbird",
            "vlc",
            "gimp",
            "inkscape",
            "rhythmbox",
            "evince",
            "eog",
        ]

        for bin_path in bin_paths:
            if not bin_path.exists():
                continue

            for executable in bin_path.iterdir():
                if not executable.is_file():
                    continue

                name = executable.name

                # Skip if already added or not a common app
                if name in [a.executable for a in apps]:
                    continue

                # Check if it's a GUI application
                if self._is_gui_executable(executable):
                    category = self.categorizer.get_category(name)
                    apps.append(
                        AppInfo(
                            name=name,
                            executable=name,
                            display_name=self._format_name(name),
                            categories=[category.value] if category else [],
                        )
                    )

        return apps

    def _executable_exists(self, name: str) -> bool:
        """Check if an executable exists in PATH."""
        return os.system(f"command -v {name} > /dev/null 2>&1") == 0

    def _is_gui_executable(self, path: Path) -> bool:
        """Check if a file is likely a GUI application."""
        try:
            # Check if it's executable
            if not os.access(path, os.X_OK):
                return False

            # Check if it's a binary (not a script)
            with open(path, "rb") as f:
                magic = f.read(4)
                # ELF binary
                if magic == b"\x7fELF":
                    return True

            return False
        except (IOError, OSError):
            return False

    def _format_name(self, name: str) -> str:
        """Format a package name for display."""
        # Replace dashes and underscores with spaces
        name = name.replace("-", " ").replace("_", " ")
        # Capitalize first letter of each word
        return name.title()

    def _parse_desktop_file(self, desktop_file: Path) -> dict:
        """Parse a .desktop file."""
        info = {}

        try:
            with open(desktop_file, "r", encoding="utf-8", errors="ignore") as f:
                in_desktop_entry = False
                for line in f:
                    line = line.strip()
                    if line == "[Desktop Entry]":
                        in_desktop_entry = True
                        continue
                    elif line.startswith("[") and in_desktop_entry:
                        break

                    if in_desktop_entry and "=" in line:
                        key, value = line.split("=", 1)
                        info[key.strip()] = value.strip()
        except Exception:
            pass

        return info

    def refresh(self) -> None:
        """Clear the detection cache."""
        self._cache = None
        self.app_cache.clear()
        logger.info("App detection cache cleared for Fedora")
