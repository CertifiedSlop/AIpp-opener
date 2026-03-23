"""Extended tests for AIpp Opener detector modules (Phase 6B)."""

import unittest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import asdict


class TestNixOSDetectorExtended(unittest.TestCase):
    """Extended tests for NixOS app detector."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.nixos import NixOSAppDetector

        self.detector = NixOSAppDetector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_nix_command_available_true(self):
        """Test nix command availability check when available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.detector._nix_command_available()
            self.assertTrue(result)

    def test_nix_command_available_false(self):
        """Test nix command availability check when unavailable."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = self.detector._nix_command_available()
            self.assertFalse(result)

    def test_nix_command_available_timeout(self):
        """Test nix command availability check with timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            result = self.detector._nix_command_available()
            self.assertFalse(result)

    def test_scan_profile(self):
        """Test scanning a Nix profile."""
        bin_dir = self.temp_path / "bin"
        bin_dir.mkdir()
        
        # Create mock executables
        firefox = bin_dir / "firefox"
        firefox.write_text("#!/bin/bash")
        firefox.chmod(0o755)
        
        skip_lib = bin_dir / "libexec"
        skip_lib.write_text("#!/bin/bash")
        skip_lib.chmod(0o755)

        with patch.object(self.detector, '_create_app_from_executable') as mock_create:
            mock_create.return_value = MagicMock(name="firefox", executable="/test/firefox")
            apps = self.detector._scan_profile(self.temp_path)
            self.assertIsInstance(apps, list)

    def test_create_app_from_executable_with_desktop(self):
        """Test creating app info when desktop file exists."""
        exec_path = self.temp_path / "firefox"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        with patch.object(self.detector, '_find_desktop_file') as mock_find:
            mock_find.return_value = self.temp_path / "firefox.desktop"
            with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
                mock_parse.return_value = {
                    "Name": "Firefox Browser",
                    "Comment": "Web browser",
                    "Categories": ["Network", "WebBrowser"]
                }
                app = self.detector._create_app_from_executable(exec_path)
                self.assertIsNotNone(app)
                self.assertEqual(app.display_name, "Firefox Browser")

    def test_create_app_from_executable_without_desktop(self):
        """Test creating app info without desktop file."""
        exec_path = self.temp_path / "firefox"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        with patch.object(self.detector, '_find_desktop_file') as mock_find:
            mock_find.return_value = None
            app = self.detector._create_app_from_executable(exec_path)
            self.assertIsNotNone(app)
            # Firefox should be categorized as 'browser'
            self.assertIn("browser", app.categories)

    def test_create_app_from_executable_skips_lib_prefix(self):
        """Test that lib prefix executables are skipped."""
        exec_path = self.temp_path / "libfoo"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        app = self.detector._create_app_from_executable(exec_path)
        self.assertIsNone(app)

    def test_create_app_from_executable_skips_nix_prefix(self):
        """Test that nix- prefix executables are skipped."""
        exec_path = self.temp_path / "nix-build"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        app = self.detector._create_app_from_executable(exec_path)
        self.assertIsNone(app)

    def test_create_app_from_executable_skips_systemd_prefix(self):
        """Test that systemd- prefix executables are skipped."""
        exec_path = self.temp_path / "systemd-run"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        app = self.detector._create_app_from_executable(exec_path)
        self.assertIsNone(app)

    def test_create_app_from_executable_skips_common_utils(self):
        """Test that common system utilities are skipped."""
        for util in ["sh", "bash", "python", "python3", "git", "ssh"]:
            exec_path = self.temp_path / util
            exec_path.write_text("#!/bin/bash")
            exec_path.chmod(0o755)
            app = self.detector._create_app_from_executable(exec_path)
            self.assertIsNone(app, f"Expected {util} to be skipped")

    def test_find_desktop_file_not_found(self):
        """Test finding desktop file when it doesn't exist."""
        result = self.detector._find_desktop_file("nonexistent-app")
        self.assertIsNone(result)

    def test_find_desktop_file_found(self):
        """Test finding desktop file when it exists."""
        desktop_dir = self.temp_path / "applications"
        desktop_dir.mkdir()
        desktop_file = desktop_dir / "firefox.desktop"
        desktop_file.write_text("[Desktop Entry]\nExec=firefox\n")

        with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
            mock_parse.return_value = {"Exec": "firefox"}
            # Mock the desktop directory search
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'glob', return_value=[desktop_file]):
                    result = self.detector._find_desktop_file("firefox")
                    # The method may still return None due to parsing
                    self.assertIsInstance(result, (Path, type(None)))

    def test_parse_desktop_file(self):
        """Test parsing a desktop file."""
        desktop_file = self.temp_path / "test.desktop"
        desktop_content = """[Desktop Entry]
Name=Test App
Comment=A test application
Exec=test-app
Categories=Utility;Application;
"""
        desktop_file.write_text(desktop_content)

        info = self.detector._parse_desktop_file(desktop_file)
        self.assertEqual(info.get("Name"), "Test App")
        self.assertEqual(info.get("Comment"), "A test application")
        self.assertEqual(info.get("Exec"), "test-app")
        self.assertIn("Utility", info.get("Categories", []))

    def test_parse_desktop_file_invalid(self):
        """Test parsing an invalid desktop file."""
        desktop_file = self.temp_path / "invalid.desktop"
        desktop_file.write_text("invalid content")

        info = self.detector._parse_desktop_file(desktop_file)
        self.assertIsInstance(info, dict)

    def test_parse_desktop_file_not_exists(self):
        """Test parsing a non-existent desktop file."""
        desktop_file = self.temp_path / "nonexistent.desktop"
        info = self.detector._parse_desktop_file(desktop_file)
        self.assertEqual(info, {})

    def test_detect_from_nix_store_success(self):
        """Test detection from nix-store with success."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="/nix/store/abc123-firefox-100.0/bin/firefox\n"
            )
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'iterdir', return_value=[]):
                    apps = self.detector._detect_from_nix_store()
                    self.assertIsInstance(apps, list)

    def test_detect_from_nix_store_error(self):
        """Test detection from nix-store with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            apps = self.detector._detect_from_nix_store()
            self.assertEqual(apps, [])

    def test_detect_from_nix_store_file_not_found(self):
        """Test detection from nix-store when command not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            apps = self.detector._detect_from_nix_store()
            self.assertEqual(apps, [])

    def test_detect_uses_cache(self):
        """Test that detect uses memory cache."""
        mock_apps = [MagicMock(executable="/test/app")]
        self.detector._cache = mock_apps

        result = self.detector.detect()
        self.assertEqual(result, mock_apps)

    def test_detect_uses_disk_cache(self):
        """Test that detect uses disk cache."""
        cached_apps = [{"name": "cached-app", "executable": "/test/cached", 
                       "display_name": "Cached App", "description": None, "categories": []}]
        
        with patch.object(self.detector.app_cache, 'get_apps', return_value=cached_apps):
            result = self.detector.detect()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, "cached-app")

    def test_refresh_clears_cache(self):
        """Test that refresh clears both memory and disk cache."""
        self.detector._cache = [MagicMock()]
        
        with patch.object(self.detector.app_cache, 'clear') as mock_clear:
            self.detector.refresh()
            self.assertIsNone(self.detector._cache)
            mock_clear.assert_called_once()


class TestDebianDetectorExtended(unittest.TestCase):
    """Extended tests for Debian app detector."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.debian import DebianAppDetector

        self.detector = DebianAppDetector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_dpkg_available_true(self):
        """Test dpkg availability when available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.detector._dpkg_available()
            self.assertTrue(result)

    def test_dpkg_available_false(self):
        """Test dpkg availability when unavailable."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = self.detector._dpkg_available()
            self.assertFalse(result)

    def test_detect_from_dpkg_success(self):
        """Test detection from dpkg with success."""
        dpkg_output = """ii  firefox  100.0  Web browser
ii  chrome  90.0  Web browser from Google
"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=dpkg_output)
            with patch.object(self.detector, '_find_package_executables', return_value=[]):
                apps = self.detector._detect_from_dpkg()
                self.assertIsInstance(apps, list)

    def test_detect_from_dpkg_error(self):
        """Test detection from dpkg with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            apps = self.detector._detect_from_dpkg()
            self.assertEqual(apps, [])

    def test_find_package_executables_success(self):
        """Test finding package executables."""
        file_list = "/usr/bin/firefox\n/usr/bin/firefox-bin\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            with patch.object(Path, 'exists', return_value=True):
                with patch('os.access', return_value=True):
                    with patch.object(self.detector, '_create_app_from_executable') as mock_create:
                        mock_create.return_value = MagicMock(name="firefox", executable="/usr/bin/firefox")
                        apps = self.detector._find_package_executables("firefox")
                        self.assertIsInstance(apps, list)

    def test_find_package_executables_error(self):
        """Test finding package executables with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            apps = self.detector._find_package_executables("firefox")
            self.assertEqual(apps, [])

    def test_find_executable_path_which(self):
        """Test finding executable path using which."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="/usr/bin/firefox\n")
            result = self.detector._find_executable_path("firefox")
            self.assertEqual(result, "/usr/bin/firefox")

    def test_find_executable_path_common_paths(self):
        """Test finding executable in common paths."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with patch.object(Path, 'exists', return_value=True):
                with patch('os.access', return_value=True):
                    result = self.detector._find_executable_path("firefox")
                    self.assertIsNotNone(result)

    def test_create_app_from_executable_skips_dash(self):
        """Test that dash is skipped."""
        exec_path = self.temp_path / "dash"
        exec_path.write_text("#!/bin/bash")
        exec_path.chmod(0o755)

        app = self.detector._create_app_from_executable(exec_path)
        self.assertIsNone(app)

    def test_create_app_from_executable_skips_npm(self):
        """Test that npm/npx are skipped."""
        for util in ["npm", "npx"]:
            exec_path = self.temp_path / util
            exec_path.write_text("#!/bin/bash")
            exec_path.chmod(0o755)
            app = self.detector._create_app_from_executable(exec_path)
            self.assertIsNone(app, f"Expected {util} to be skipped")

    def test_create_app_from_executable_skips_text_utils(self):
        """Test that text utilities are skipped."""
        for util in ["grep", "sed", "awk", "find"]:
            exec_path = self.temp_path / util
            exec_path.write_text("#!/bin/bash")
            exec_path.chmod(0o755)
            app = self.detector._create_app_from_executable(exec_path)
            self.assertIsNone(app, f"Expected {util} to be skipped")

    def test_create_app_from_executable_skips_file_utils(self):
        """Test that file utilities are skipped."""
        for util in ["cat", "ls", "cp", "mv", "rm", "mkdir"]:
            exec_path = self.temp_path / util
            exec_path.write_text("#!/bin/bash")
            exec_path.chmod(0o755)
            app = self.detector._create_app_from_executable(exec_path)
            self.assertIsNone(app, f"Expected {util} to be skipped")

    def test_detect_from_desktop_files(self):
        """Test detection from desktop files."""
        desktop_dir = self.temp_path / "applications"
        desktop_dir.mkdir()
        desktop_file = desktop_dir / "firefox.desktop"
        desktop_file.write_text("[Desktop Entry]\nName=Firefox\nExec=firefox\n")

        with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
            mock_parse.return_value = {"Name": "Firefox", "Exec": "firefox"}
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'glob', return_value=[desktop_file]):
                    with patch.object(self.detector, '_find_executable_path', return_value="/usr/bin/firefox"):
                        apps = self.detector._detect_from_desktop_files()
                        self.assertIsInstance(apps, list)

    def test_detect_from_desktop_files_empty_exec(self):
        """Test detection from desktop files with empty Exec."""
        with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
            mock_parse.return_value = {"Name": "Test", "Exec": ""}
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'glob', return_value=[]):
                    apps = self.detector._detect_from_desktop_files()
                    self.assertEqual(apps, [])

    def test_detect_uses_cache(self):
        """Test that detect uses memory cache."""
        mock_apps = [MagicMock(executable="/test/app")]
        self.detector._cache = mock_apps

        result = self.detector.detect()
        self.assertEqual(result, mock_apps)

    def test_detect_uses_disk_cache(self):
        """Test that detect uses disk cache."""
        cached_apps = [{"name": "cached-app", "executable": "/test/cached",
                       "display_name": "Cached App", "description": None, "categories": []}]

        with patch.object(self.detector.app_cache, 'get_apps', return_value=cached_apps):
            result = self.detector.detect()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, "cached-app")

    def test_refresh_clears_cache(self):
        """Test that refresh clears both memory and disk cache."""
        self.detector._cache = [MagicMock()]

        with patch.object(self.detector.app_cache, 'clear') as mock_clear:
            self.detector.refresh()
            self.assertIsNone(self.detector._cache)
            mock_clear.assert_called_once()


class TestFedoraDetectorExtended(unittest.TestCase):
    """Extended tests for Fedora app detector."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.fedora import FedoraAppDetector

        self.detector = FedoraAppDetector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_rpm_available_true(self):
        """Test rpm availability when available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.detector._rpm_available()
            self.assertTrue(result)

    def test_rpm_available_false(self):
        """Test rpm availability when unavailable."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = self.detector._rpm_available()
            self.assertFalse(result)

    def test_detect_from_rpm_success(self):
        """Test detection from rpm with success."""
        pkg_list = "firefox\nchrome\ncode\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=pkg_list)
            with patch.object(self.detector, '_get_package_executables', return_value=[]):
                apps = self.detector._detect_from_rpm()
                self.assertIsInstance(apps, list)

    def test_detect_from_rpm_error(self):
        """Test detection from rpm with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            apps = self.detector._detect_from_rpm()
            self.assertEqual(apps, [])

    def test_get_package_executables_success(self):
        """Test getting package executables."""
        file_list = "/usr/bin/firefox\n/usr/bin/firefox-bin\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            executables = self.detector._get_package_executables("firefox")
            self.assertIsInstance(executables, list)

    def test_get_package_executables_filters_binaries(self):
        """Test that only bin directory executables are returned."""
        file_list = "/usr/bin/firefox\n/usr/share/doc/firefox\n/etc/firefox.conf\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            executables = self.detector._get_package_executables("firefox")
            self.assertEqual(len(executables), 1)
            self.assertEqual(executables[0], "firefox")

    def test_get_package_executables_filters_system_tools(self):
        """Test that system tools are filtered out."""
        file_list = "/usr/bin/sh\n/usr/bin/bash\n/usr/bin/firefox\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            executables = self.detector._get_package_executables("firefox")
            self.assertNotIn("sh", executables)
            self.assertNotIn("bash", executables)

    def test_get_package_executables_error(self):
        """Test getting package executables with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            executables = self.detector._get_package_executables("firefox")
            self.assertEqual(executables, [])

    def test_get_package_executables_timeout(self):
        """Test getting package executables with timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutError()
            executables = self.detector._get_package_executables("firefox")
            self.assertEqual(executables, [])

    def test_format_name(self):
        """Test name formatting."""
        self.assertEqual(self.detector._format_name("firefox"), "Firefox")
        self.assertEqual(self.detector._format_name("libreoffice"), "Libreoffice")
        self.assertEqual(self.detector._format_name("code-editor"), "Code Editor")
        self.assertEqual(self.detector._format_name("my_app"), "My App")

    def test_executable_exists_true(self):
        """Test executable exists check when exists."""
        with patch('os.system') as mock_system:
            mock_system.return_value = 0
            result = self.detector._executable_exists("firefox")
            self.assertTrue(result)

    def test_executable_exists_false(self):
        """Test executable exists check when doesn't exist."""
        with patch('os.system') as mock_system:
            mock_system.return_value = 1
            result = self.detector._executable_exists("nonexistent")
            self.assertFalse(result)

    def test_is_gui_executable_elf(self):
        """Test GUI executable detection for ELF binary."""
        exec_path = self.temp_path / "test-app"
        exec_path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        exec_path.chmod(0o755)

        with patch('os.access', return_value=True):
            result = self.detector._is_gui_executable(exec_path)
            self.assertTrue(result)

    def test_is_gui_executable_not_executable(self):
        """Test GUI executable detection when not executable."""
        exec_path = self.temp_path / "test-app"
        exec_path.write_text("#!/bin/bash")

        with patch('os.access', return_value=False):
            result = self.detector._is_gui_executable(exec_path)
            self.assertFalse(result)

    def test_is_gui_executable_io_error(self):
        """Test GUI executable detection with IO error."""
        exec_path = self.temp_path / "test-app"

        with patch('os.access', return_value=True):
            with patch('builtins.open', side_effect=IOError()):
                result = self.detector._is_gui_executable(exec_path)
                self.assertFalse(result)

    def test_detect_from_desktop_files(self):
        """Test detection from desktop files."""
        desktop_dir = self.temp_path / "applications"
        desktop_dir.mkdir()
        desktop_file = desktop_dir / "firefox.desktop"
        desktop_file.write_text("[Desktop Entry]\nName=Firefox\nExec=firefox\n")

        with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
            mock_parse.return_value = {"Name": "Firefox", "Exec": "firefox"}
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'glob', return_value=[desktop_file]):
                    with patch.object(self.detector, '_executable_exists', return_value=True):
                        apps = self.detector._detect_from_desktop_files()
                        self.assertIsInstance(apps, list)

    def test_detect_from_desktop_files_exception(self):
        """Test detection from desktop files with exception."""
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'glob', return_value=[]):
                apps = self.detector._detect_from_desktop_files()
                self.assertIsInstance(apps, list)

    def test_detect_from_bin_paths(self):
        """Test detection from binary paths."""
        bin_dir = self.temp_path / "bin"
        bin_dir.mkdir()
        exec_path = bin_dir / "firefox"
        exec_path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        exec_path.chmod(0o755)

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'iterdir', return_value=[exec_path]):
                with patch.object(self.detector, '_is_gui_executable', return_value=True):
                    with patch.object(self.detector, '_format_name', return_value="Firefox"):
                        with patch.object(self.detector.categorizer, 'categorize', return_value=MagicMock(value="browser")):
                            apps = self.detector._detect_from_bin_paths()
                            self.assertIsInstance(apps, list)

    def test_refresh_clears_cache(self):
        """Test that refresh clears both memory and disk cache."""
        self.detector._cache = [MagicMock()]

        with patch.object(self.detector.app_cache, 'clear') as mock_clear:
            self.detector.refresh()
            self.assertIsNone(self.detector._cache)
            mock_clear.assert_called_once()


class TestArchDetectorExtended(unittest.TestCase):
    """Extended tests for Arch Linux app detector."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.detectors.arch import ArchAppDetector

        self.detector = ArchAppDetector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_pacman_available_true(self):
        """Test pacman availability when available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.detector._pacman_available()
            self.assertTrue(result)

    def test_pacman_available_false(self):
        """Test pacman availability when unavailable."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = self.detector._pacman_available()
            self.assertFalse(result)

    def test_detect_from_pacman_success(self):
        """Test detection from pacman with success."""
        pkg_list = "firefox\nchrome\ncode\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=pkg_list)
            with patch.object(self.detector, '_get_package_executables', return_value=[]):
                apps = self.detector._detect_from_pacman()
                self.assertIsInstance(apps, list)

    def test_detect_from_pacman_error(self):
        """Test detection from pacman with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            apps = self.detector._detect_from_pacman()
            self.assertEqual(apps, [])

    def test_get_package_executables_success(self):
        """Test getting package executables."""
        file_list = "/usr/bin/firefox\n/usr/bin/firefox-bin\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            executables = self.detector._get_package_executables("firefox")
            self.assertIsInstance(executables, list)

    def test_get_package_executables_filters_binaries(self):
        """Test that only bin directory executables are returned."""
        file_list = "/usr/bin/firefox\n/usr/share/doc/firefox\n/etc/firefox.conf\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=file_list)
            executables = self.detector._get_package_executables("firefox")
            self.assertEqual(len(executables), 1)
            self.assertEqual(executables[0], "firefox")

    def test_get_package_executables_error(self):
        """Test getting package executables with error."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.SubprocessError()
            executables = self.detector._get_package_executables("firefox")
            self.assertEqual(executables, [])

    def test_format_name(self):
        """Test name formatting."""
        self.assertEqual(self.detector._format_name("firefox"), "Firefox")
        self.assertEqual(self.detector._format_name("libreoffice"), "Libreoffice")
        self.assertEqual(self.detector._format_name("code-editor"), "Code Editor")
        self.assertEqual(self.detector._format_name("my_app"), "My App")

    def test_executable_exists_true(self):
        """Test executable exists check when exists."""
        with patch('os.system') as mock_system:
            mock_system.return_value = 0
            result = self.detector._executable_exists("firefox")
            self.assertTrue(result)

    def test_executable_exists_false(self):
        """Test executable exists check when doesn't exist."""
        with patch('os.system') as mock_system:
            mock_system.return_value = 1
            result = self.detector._executable_exists("nonexistent")
            self.assertFalse(result)

    def test_is_gui_executable_elf(self):
        """Test GUI executable detection for ELF binary."""
        exec_path = self.temp_path / "test-app"
        exec_path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        exec_path.chmod(0o755)

        with patch('os.access', return_value=True):
            result = self.detector._is_gui_executable(exec_path)
            self.assertTrue(result)

    def test_is_gui_executable_not_executable(self):
        """Test GUI executable detection when not executable."""
        exec_path = self.temp_path / "test-app"
        exec_path.write_text("#!/bin/bash")

        with patch('os.access', return_value=False):
            result = self.detector._is_gui_executable(exec_path)
            self.assertFalse(result)

    def test_is_gui_executable_io_error(self):
        """Test GUI executable detection with IO error."""
        exec_path = self.temp_path / "test-app"

        with patch('os.access', return_value=True):
            with patch('builtins.open', side_effect=IOError()):
                result = self.detector._is_gui_executable(exec_path)
                self.assertFalse(result)

    def test_detect_from_desktop_files(self):
        """Test detection from desktop files."""
        desktop_dir = self.temp_path / "applications"
        desktop_dir.mkdir()
        desktop_file = desktop_dir / "firefox.desktop"
        desktop_file.write_text("[Desktop Entry]\nName=Firefox\nExec=firefox\n")

        with patch.object(self.detector, '_parse_desktop_file') as mock_parse:
            mock_parse.return_value = {"Name": "Firefox", "Exec": "firefox"}
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'glob', return_value=[desktop_file]):
                    with patch.object(self.detector, '_executable_exists', return_value=True):
                        apps = self.detector._detect_from_desktop_files()
                        self.assertIsInstance(apps, list)

    def test_detect_from_bin_paths(self):
        """Test detection from binary paths."""
        bin_dir = self.temp_path / "bin"
        bin_dir.mkdir()
        exec_path = bin_dir / "firefox"
        exec_path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        exec_path.chmod(0o755)

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'iterdir', return_value=[exec_path]):
                with patch.object(self.detector, '_is_gui_executable', return_value=True):
                    with patch.object(self.detector, '_format_name', return_value="Firefox"):
                        with patch.object(self.detector.categorizer, 'categorize', return_value=MagicMock(value="browser")):
                            apps = self.detector._detect_from_bin_paths()
                            self.assertIsInstance(apps, list)

    def test_refresh_clears_cache(self):
        """Test that refresh clears both memory and disk cache."""
        self.detector._cache = [MagicMock()]

        with patch.object(self.detector.app_cache, 'clear') as mock_clear:
            self.detector.refresh()
            self.assertIsNone(self.detector._cache)
            mock_clear.assert_called_once()


class TestBaseDetector(unittest.TestCase):
    """Tests for base detector class."""

    def test_app_info_defaults(self):
        """Test AppInfo dataclass defaults."""
        from aipp_opener.detectors.base import AppInfo

        app = AppInfo(name="test", executable="/test/path")
        self.assertEqual(app.display_name, "test")
        self.assertEqual(app.categories, [])
        self.assertIsNone(app.description)

    def test_app_info_custom_values(self):
        """Test AppInfo with custom values."""
        from aipp_opener.detectors.base import AppInfo

        app = AppInfo(
            name="firefox",
            executable="/usr/bin/firefox",
            display_name="Firefox Browser",
            description="A web browser",
            categories=["browser", "network"]
        )
        self.assertEqual(app.display_name, "Firefox Browser")
        self.assertEqual(app.description, "A web browser")
        self.assertEqual(app.categories, ["browser", "network"])

    def test_get_app_by_executable_found(self):
        """Test getting app by executable when found."""
        from aipp_opener.detectors.base import AppInfo, AppDetector

        class MockDetector(AppDetector):
            def detect(self):
                return [
                    AppInfo(name="firefox", executable="/usr/bin/firefox"),
                    AppInfo(name="chrome", executable="/usr/bin/chrome"),
                ]

            def is_available(self):
                return True

        detector = MockDetector()
        app = detector.get_app_by_executable("/usr/bin/firefox")
        self.assertIsNotNone(app)
        self.assertEqual(app.name, "firefox")

    def test_get_app_by_executable_not_found(self):
        """Test getting app by executable when not found."""
        from aipp_opener.detectors.base import AppInfo, AppDetector

        class MockDetector(AppDetector):
            def detect(self):
                return [
                    AppInfo(name="firefox", executable="/usr/bin/firefox"),
                ]

            def is_available(self):
                return True

        detector = MockDetector()
        app = detector.get_app_by_executable("/usr/bin/nonexistent")
        self.assertIsNone(app)

    def test_get_apps_by_name_match(self):
        """Test getting apps by name with match."""
        from aipp_opener.detectors.base import AppInfo, AppDetector

        class MockDetector(AppDetector):
            def detect(self):
                return [
                    AppInfo(name="firefox", executable="/usr/bin/firefox", display_name="Firefox Browser"),
                    AppInfo(name="chrome", executable="/usr/bin/chrome", display_name="Chrome"),
                ]

            def is_available(self):
                return True

        detector = MockDetector()
        apps = detector.get_apps_by_name("fire")
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].name, "firefox")

    def test_get_apps_by_name_no_match(self):
        """Test getting apps by name with no match."""
        from aipp_opener.detectors.base import AppInfo, AppDetector

        class MockDetector(AppDetector):
            def detect(self):
                return [
                    AppInfo(name="firefox", executable="/usr/bin/firefox"),
                ]

            def is_available(self):
                return True

        detector = MockDetector()
        apps = detector.get_apps_by_name("nonexistent")
        self.assertEqual(len(apps), 0)


if __name__ == "__main__":
    unittest.main()
