"""
Sample plugin for AIpp Opener - Custom Commands.

This plugin adds useful custom commands to AIpp Opener.

Installation:
    Copy this file to ~/.local/share/aipp_opener/plugins/custom_commands.py

Usage:
    After installation, run:
    python -m aipp_opener --plugins  # List plugins
    python -m aipp_opener --enable-plugin custom_commands

Available Commands:
    - system_update: Update system packages
    - clear_cache: Clear application caches
    - show_ip: Show public IP address
    - weather: Show weather information

Author: AIpp Opener Team
License: MIT
"""

import subprocess
import webbrowser
from typing import Callable

from aipp_opener.plugins import CommandPlugin


class CustomCommandsPlugin(CommandPlugin):
    """Adds custom system commands."""

    @property
    def name(self) -> str:
        return "custom_commands"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Adds useful system commands: system_update, clear_cache, show_ip, weather"

    def get_commands(self) -> dict[str, Callable]:
        """Return available commands."""
        return {
            "system_update": self.system_update,
            "clear_cache": self.clear_cache,
            "show_ip": self.show_ip,
            "weather": self.weather,
        }

    def system_update(self) -> None:
        """
        Update system packages.

        Detects the package manager and runs the appropriate update command.
        Opens a terminal to show progress.
        """
        import os

        # Detect package manager
        update_commands = {
            "apt": "sudo apt update && sudo apt upgrade -y",
            "dnf": "sudo dnf upgrade -y",
            "pacman": "sudo pacman -Syu --noconfirm",
            "nix-env": "nix-channel --update",
        }

        # Try to detect which package manager is available
        for pkg_manager, command in update_commands.items():
            try:
                result = subprocess.run(
                    ["which", pkg_manager],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Open terminal with the update command
                    self._run_in_terminal(command)
                    print(f"System update started with {pkg_manager}")
                    return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        print("No supported package manager found")

    def clear_cache(self) -> None:
        """
        Clear application caches.

        Clears common cache directories:
        - ~/.cache
        - Python pip cache
        - npm cache
        """
        import os
        from pathlib import Path

        cache_dirs = [
            Path.home() / ".cache",
            Path.home() / ".local" / "cache",
        ]

        cleared = 0
        total_size = 0

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    # Calculate size before clearing
                    dir_size = sum(
                        f.stat().st_size for f in cache_dir.rglob("*") if f.is_file()
                    )
                    total_size += dir_size

                    # Clear the cache
                    subprocess.run(
                        ["rm", "-rf", str(cache_dir) + "/*"],
                        capture_output=True,
                        timeout=30
                    )
                    cleared += 1
                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    print(f"Error clearing {cache_dir}: {e}")

        # Clear pip cache
        try:
            subprocess.run(
                ["pip", "cache", "purge"],
                capture_output=True,
                timeout=30
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Clear npm cache
        try:
            subprocess.run(
                ["npm", "cache", "clean", "--force"],
                capture_output=True,
                timeout=30
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        print(f"Cleared {cleared} cache directories, freed ~{total_size / 1024 / 1024:.1f} MB")

    def show_ip(self) -> None:
        """Show public IP address."""
        try:
            # Use a simple API to get public IP
            result = subprocess.run(
                ["curl", "-s", "https://api.ipify.org"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                print(f"Your public IP address: {result.stdout.strip()}")
            else:
                # Fallback to another service
                result = subprocess.run(
                    ["curl", "-s", "https://ifconfig.me"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"Your public IP address: {result.stdout.strip()}")
                else:
                    print("Could not determine public IP address")

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error getting IP address: {e}")

    def weather(self) -> None:
        """Show weather information."""
        try:
            # Use wttr.in for weather information
            result = subprocess.run(
                ["curl", "-s", "wttr.in"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print("Could not fetch weather information")

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error getting weather: {e}")

    def _run_in_terminal(self, command: str) -> None:
        """Run a command in a terminal emulator."""
        terminal_commands = [
            ["gnome-terminal", "--", "bash", "-c", command + "; exec bash"],
            ["konsole", "-e", "bash", "-c", command + "; exec bash"],
            ["xfce4-terminal", "-e", command + "; exec bash"],
            ["alacritty", "-e", "bash", "-c", command + "; exec bash"],
            ["kitty", "-e", "bash", "-c", command + "; exec bash"],
        ]

        for terminal_cmd in terminal_commands:
            try:
                result = subprocess.run(
                    ["which", terminal_cmd[0]],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    subprocess.Popen(terminal_cmd)
                    return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        # Fallback: try to open web browser with explanation
        print(f"Run this command manually: {command}")


# Export the plugin class
__all__ = ["CustomCommandsPlugin"]
