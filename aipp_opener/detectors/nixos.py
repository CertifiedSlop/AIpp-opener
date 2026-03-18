"""NixOS-specific application detector."""

import subprocess
import json
import os
from pathlib import Path
from typing import Optional

from aipp_opener.detectors.base import AppDetector, AppInfo
from aipp_opener.categories import AppCategorizer, AppCategory


class NixOSAppDetector(AppDetector):
    """Detects applications installed on NixOS systems."""

    def __init__(self):
        self._cache: Optional[list[AppInfo]] = None
        self.categorizer = AppCategorizer()

    def is_available(self) -> bool:
        """Check if running on NixOS."""
        # Check for NixOS-specific files/commands
        return (
            Path("/run/current-system").exists() or
            Path("/nix/var/nix/profiles").exists() or
            self._nix_command_available()
        )

    def _nix_command_available(self) -> bool:
        """Check if nix command is available."""
        try:
            result = subprocess.run(
                ["nix", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def detect(self) -> list[AppInfo]:
        """Detect applications from Nix profiles."""
        if self._cache is not None:
            return self._cache

        apps = []
        seen_executables = set()

        # Method 1: Check user profile
        apps.extend(self._detect_from_profile())

        # Method 2: Check system profile
        apps.extend(self._detect_from_system_profile())

        # Method 3: Use nix-store query for installed packages
        apps.extend(self._detect_from_nix_store())

        # Method 4: Scan common binary directories
        apps.extend(self._detect_from_bin_paths())

        # Deduplicate by executable
        unique_apps = []
        for app in apps:
            if app.executable not in seen_executables:
                seen_executables.add(app.executable)
                unique_apps.append(app)

        self._cache = unique_apps
        return unique_apps

    def _detect_from_profile(self) -> list[AppInfo]:
        """Detect apps from user's Nix profile."""
        apps = []
        profile_path = Path.home() / ".nix-profile"

        if profile_path.exists():
            apps.extend(self._scan_profile(profile_path))

        return apps

    def _detect_from_system_profile(self) -> list[AppInfo]:
        """Detect apps from system profile."""
        apps = []
        system_profile = Path("/run/current-system/sw")

        if system_profile.exists():
            apps.extend(self._scan_profile(system_profile))

        return apps

    def _scan_profile(self, profile_path: Path) -> list[AppInfo]:
        """Scan a Nix profile for applications."""
        apps = []
        bin_path = profile_path / "bin"

        if bin_path.exists():
            for executable in bin_path.iterdir():
                if executable.is_file() and os.access(executable, os.X_OK):
                    app = self._create_app_from_executable(executable)
                    if app:
                        apps.append(app)

        return apps

    def _detect_from_nix_store(self) -> list[AppInfo]:
        """Detect apps using nix-store query."""
        apps = []

        try:
            # Query installed packages
            result = subprocess.run(
                ["nix-store", "-q", "--installed"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                for package_path in result.stdout.strip().split("\n"):
                    if package_path:
                        pkg_path = Path(package_path)
                        bin_path = pkg_path / "bin"
                        if bin_path.exists():
                            for executable in bin_path.iterdir():
                                if executable.is_file() and os.access(executable, os.X_OK):
                                    app = self._create_app_from_executable(executable)
                                    if app:
                                        apps.append(app)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return apps

    def _detect_from_bin_paths(self) -> list[AppInfo]:
        """Detect apps from standard binary paths."""
        apps = []
        bin_paths = [
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/bin"),
            Path.home() / ".local" / "bin",
        ]

        for bin_path in bin_paths:
            if bin_path.exists():
                for executable in bin_path.iterdir():
                    if executable.is_file() and os.access(executable, os.X_OK):
                        app = self._create_app_from_executable(executable)
                        if app:
                            apps.append(app)

        return apps

    def _create_app_from_executable(self, executable: Path) -> Optional[AppInfo]:
        """Create an AppInfo from an executable file."""
        name = executable.name

        # Skip common non-GUI utilities
        skip_prefixes = ["lib", "libexec", "nix-", "systemd-", "ld-", "libnss_"]
        if any(name.startswith(p) for p in skip_prefixes):
            return None

        # Skip if it's a common system utility without GUI
        skip_names = {"sh", "bash", "python", "python3", "perl", "ruby", "node",
                      "npm", "nix", "git", "ssh", "scp", "rsync"}
        if name in skip_names:
            return None

        # Try to get desktop file for more info
        display_name = None
        description = None
        categories = []

        desktop_file = self._find_desktop_file(name)
        if desktop_file:
            info = self._parse_desktop_file(desktop_file)
            display_name = info.get("Name")
            description = info.get("Comment")
            categories = info.get("Categories", [])
        else:
            # Auto-categorize based on name
            category = self.categorizer.categorize(name)
            categories = [category.value] if category != AppCategory.OTHER else []

        return AppInfo(
            name=name,
            executable=str(executable),
            display_name=display_name or name.title(),
            description=description,
            categories=categories
        )

    def _find_desktop_file(self, app_name: str) -> Optional[Path]:
        """Find .desktop file for an application."""
        desktop_dirs = [
            Path.home() / ".local" / "share" / "applications",
            Path("/usr/share/applications"),
            Path("/run/current-system/sw/share/applications"),
        ]

        # Normalize app name for matching
        normalized = app_name.lower().replace("-", "").replace("_", "")

        for desktop_dir in desktop_dirs:
            if not desktop_dir.exists():
                continue

            for desktop_file in desktop_dir.glob("*.desktop"):
                # Check if desktop file matches the app
                try:
                    info = self._parse_desktop_file(desktop_file)
                    exec_value = info.get("Exec", "")
                    if exec_value:
                        exec_name = exec_value.split()[0] if exec_value else ""
                        exec_normalized = exec_name.lower().replace("-", "").replace("_", "")
                        if normalized == exec_normalized or app_name.lower() == exec_name.lower():
                            return desktop_file
                except Exception:
                    continue

        return None

    def _parse_desktop_file(self, desktop_file: Path) -> dict:
        """Parse a .desktop file and extract information."""
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

        # Parse categories
        if "Categories" in info:
            info["Categories"] = info["Categories"].rstrip(";").split(";")

        return info

    def refresh(self) -> None:
        """Clear the detection cache."""
        self._cache = None
