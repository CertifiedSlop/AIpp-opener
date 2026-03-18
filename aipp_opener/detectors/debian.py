"""Debian-specific application detector."""

import subprocess
import os
from pathlib import Path
from typing import Optional

from aipp_opener.detectors.base import AppDetector, AppInfo
from aipp_opener.categories import AppCategorizer, AppCategory


class DebianAppDetector(AppDetector):
    """Detects applications installed on Debian-based systems."""

    def __init__(self):
        self._cache: Optional[list[AppInfo]] = None
        self.categorizer = AppCategorizer()
    
    def is_available(self) -> bool:
        """Check if running on a Debian-based system."""
        # Check for dpkg
        return (
            Path("/etc/debian_version").exists() or
            self._dpkg_available()
        )
    
    def _dpkg_available(self) -> bool:
        """Check if dpkg command is available."""
        try:
            result = subprocess.run(
                ["dpkg", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def detect(self) -> list[AppInfo]:
        """Detect installed applications on Debian systems."""
        if self._cache is not None:
            return self._cache
        
        apps = []
        seen_executables = set()
        
        # Method 1: Query dpkg for installed packages
        apps.extend(self._detect_from_dpkg())
        
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
        
        self._cache = unique_apps
        return unique_apps
    
    def _detect_from_dpkg(self) -> list[AppInfo]:
        """Detect apps from dpkg package database."""
        apps = []
        
        try:
            # Get list of installed packages
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("ii"):
                        parts = line.split()
                        if len(parts) >= 3:
                            package_name = parts[1]
                            package_desc = " ".join(parts[2:])
                            
                            # Try to find executables for this package
                            exec_apps = self._find_package_executables(package_name)
                            if exec_apps:
                                for app in exec_apps:
                                    if app.description is None:
                                        app.description = package_desc
                                    apps.append(app)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return apps
    
    def _find_package_executables(self, package_name: str) -> list[AppInfo]:
        """Find executables installed by a package."""
        apps = []
        
        try:
            # List files installed by the package
            result = subprocess.run(
                ["dpkg", "-L", package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for file_path in result.stdout.split("\n"):
                    if file_path.startswith("/usr/bin/") or file_path.startswith("/usr/games/"):
                        exec_path = Path(file_path)
                        if exec_path.exists() and os.access(exec_path, os.X_OK):
                            app = self._create_app_from_executable(exec_path, package_name)
                            if app:
                                apps.append(app)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return apps
    
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
                    
                    if "Exec" in info and "Name" in info:
                        exec_value = info["Exec"]
                        exec_name = exec_value.split()[0] if exec_value else ""
                        
                        # Skip if no executable name
                        if not exec_name:
                            continue
                        
                        # Find the full path to the executable
                        exec_path = self._find_executable_path(exec_name)
                        
                        app = AppInfo(
                            name=exec_name,
                            executable=exec_path or exec_name,
                            display_name=info.get("Name"),
                            description=info.get("Comment"),
                            categories=info.get("Categories", [])
                        )
                        apps.append(app)
                except Exception:
                    continue
        
        return apps
    
    def _detect_from_bin_paths(self) -> list[AppInfo]:
        """Detect apps from standard binary paths."""
        apps = []
        bin_paths = [
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/usr/games"),
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
    
    def _find_executable_path(self, exec_name: str) -> Optional[str]:
        """Find the full path to an executable."""
        try:
            result = subprocess.run(
                ["which", exec_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Check common paths
        for bin_dir in ["/usr/bin", "/usr/games", "/usr/local/bin", "/bin"]:
            exec_path = Path(bin_dir) / exec_name
            if exec_path.exists() and os.access(exec_path, os.X_OK):
                return str(exec_path)
        
        return None
    
    def _create_app_from_executable(self, executable: Path, package_name: Optional[str] = None) -> Optional[AppInfo]:
        """Create an AppInfo from an executable file."""
        name = executable.name
        
        # Skip common non-GUI utilities
        skip_prefixes = ["lib", "libexec", "ld-", "libnss_"]
        if any(name.startswith(p) for p in skip_prefixes):
            return None
        
        # Skip if it's a common system utility without GUI
        skip_names = {"sh", "bash", "dash", "python", "python3", "perl", "ruby", 
                      "node", "npm", "npx", "git", "ssh", "scp", "rsync", "grep",
                      "sed", "awk", "find", "cat", "ls", "cp", "mv", "rm", "mkdir"}
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
            Path("/usr/share/applications"),
            Path.home() / ".local" / "share" / "applications",
        ]
        
        # Normalize app name for matching
        normalized = app_name.lower().replace("-", "").replace("_", "")
        
        for desktop_dir in desktop_dirs:
            if not desktop_dir.exists():
                continue
            
            for desktop_file in desktop_dir.glob("*.desktop"):
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
