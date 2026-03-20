"""
Sample plugin for AIpp Opener - Docker App Detector.

This plugin detects Docker containers and makes them launchable as apps.

Installation:
    Copy this file to ~/.local/share/aipp_opener/plugins/docker_detector.py

Usage:
    After installation, run:
    python -m aipp_opener --plugins  # List plugins
    python -m aipp_opener --enable-plugin docker_detector

Author: AIpp Opener Team
License: MIT
"""

import subprocess
from typing import Optional
from pathlib import Path

from aipp_opener.plugins import AppDetectorPlugin
from aipp_opener.detectors.base import AppInfo
from aipp_opener.categories import AppCategory


class DockerDetectorPlugin(AppDetectorPlugin):
    """Detects running Docker containers as applications."""

    @property
    def name(self) -> str:
        return "docker_detector"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Detects running Docker containers and exposes them as launchable applications"

    def __init__(self):
        self._docker_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Docker is installed and running."""
        if self._docker_available is not None:
            return self._docker_available

        try:
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._docker_available = result.returncode == 0
            return self._docker_available
        except (subprocess.SubprocessError, FileNotFoundError):
            self._docker_available = False
            return False

    def detect(self) -> list[AppInfo]:
        """Detect running Docker containers."""
        apps = []

        if not self.is_available():
            return apps

        try:
            # Get running containers with specific format
            result = subprocess.run(
                [
                    "docker", "ps", "--format",
                    "{{.Names}}\t{{.Image}}\t{{.Ports}}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return apps

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    container_name = parts[0]
                    image = parts[1]
                    ports = parts[2] if len(parts) > 2 else ""

                    # Create a launcher script for the container
                    launcher_script = self._create_launcher(container_name)

                    if launcher_script:
                        apps.append(AppInfo(
                            name=f"docker-{container_name}",
                            executable=str(launcher_script),
                            display_name=f"Docker: {container_name}",
                            description=f"Docker container running {image}",
                            categories=[AppCategory.DEVELOPMENT.value],
                        ))

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            from aipp_opener.logger_config import get_logger
            logger = get_logger(__name__)
            logger.warning("Error detecting Docker containers: %s", e)

        return apps

    def _create_launcher(self, container_name: str) -> Optional[Path]:
        """Create a launcher script for a container."""
        from aipp_opener.logger_config import get_logger
        logger = get_logger(__name__)

        try:
            # Create cache directory for launcher scripts
            cache_dir = Path.home() / ".cache" / "aipp_opener" / "docker"
            cache_dir.mkdir(parents=True, exist_ok=True)

            launcher_path = cache_dir / f"{container_name}.sh"

            # Create launcher script
            script_content = f"""#!/bin/bash
# Auto-generated launcher for Docker container: {container_name}
exec docker exec -it {container_name} /bin/bash
"""

            with open(launcher_path, "w") as f:
                f.write(script_content)

            # Make executable
            launcher_path.chmod(0o755)

            return launcher_path

        except Exception as e:
            logger.error("Error creating Docker launcher: %s", e)
            return None

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        from aipp_opener.logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Docker Detector plugin loaded")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        from aipp_opener.logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Docker Detector plugin unloaded")


# Export the plugin class
__all__ = ["DockerDetectorPlugin"]
