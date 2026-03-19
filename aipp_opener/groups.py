"""App groups/workspaces for launching multiple apps at once."""

import json
import threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from aipp_opener.executor import AppExecutor, ExecutionResult


@dataclass
class AppGroup:
    """Represents a group of applications to launch together."""

    name: str
    apps: list[str]  # List of app names/executables
    description: str = ""
    delay: float = 0.5  # Delay between launches in seconds

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "apps": self.apps,
            "description": self.description,
            "delay": self.delay,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppGroup":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            apps=data.get("apps", []),
            description=data.get("description", ""),
            delay=data.get("delay", 0.5),
        )


class GroupManager:
    """Manages app groups/workspaces."""

    DEFAULT_GROUPS = [
        AppGroup(
            "dev",
            ["code", "gnome-terminal"],
            "Development workspace: VS Code + Terminal",
        ),
        AppGroup(
            "browse",
            ["firefox"],
            "Browsing workspace: Firefox",
        ),
        AppGroup(
            "media",
            ["spotify", "vlc"],
            "Media workspace: Spotify + VLC",
        ),
        AppGroup(
            "office",
            ["libreoffice-writer", "libreoffice-calc"],
            "Office workspace: Writer + Calc",
        ),
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the group manager.

        Args:
            config_path: Path to groups config file.
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "aipp_opener" / "groups.json"
        self.config_path = config_path
        self.groups: dict[str, AppGroup] = {}
        self._load_groups()

    def _load_groups(self) -> None:
        """Load groups from config file."""
        # Start with default groups
        for group in self.DEFAULT_GROUPS:
            self.groups[group.name.lower()] = group

        # Load user groups (can override defaults)
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    for item in data.get("groups", []):
                        group = AppGroup.from_dict(item)
                        self.groups[group.name.lower()] = group
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load groups: {e}")

    def _save_groups(self) -> None:
        """Save user groups to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Only save user-defined groups (not defaults)
        user_groups = [
            group.to_dict()
            for group in self.groups.values()
            if group not in self.DEFAULT_GROUPS
        ]

        with open(self.config_path, "w") as f:
            json.dump({"groups": user_groups}, f, indent=2)

    def add_group(
        self, name: str, apps: list[str], description: str = "", delay: float = 0.5
    ) -> bool:
        """
        Add a new app group.

        Args:
            name: Group name.
            apps: List of app names/executables.
            description: Optional description.
            delay: Delay between launches in seconds.

        Returns:
            True if added successfully.
        """
        name = name.lower().strip()
        if name in self.groups:
            return False

        group = AppGroup(name=name, apps=apps, description=description, delay=delay)
        self.groups[name] = group
        self._save_groups()
        return True

    def remove_group(self, name: str) -> bool:
        """
        Remove a group.

        Args:
            name: Group name to remove.

        Returns:
            True if removed successfully.
        """
        name = name.lower().strip()
        if name not in self.groups:
            return False

        # Don't allow removing default groups
        if self.groups[name] in self.DEFAULT_GROUPS:
            return False

        del self.groups[name]
        self._save_groups()
        return True

    def get_group(self, name: str) -> Optional[AppGroup]:
        """
        Get a group by name.

        Args:
            name: Group name.

        Returns:
            AppGroup if found, None otherwise.
        """
        return self.groups.get(name.lower().strip())

    def list_groups(self) -> list[AppGroup]:
        """Get all groups."""
        return list(self.groups.values())

    def launch_group(
        self, name: str, executor: AppExecutor
    ) -> tuple[bool, list[ExecutionResult]]:
        """
        Launch all apps in a group.

        Args:
            name: Group name.
            executor: App executor instance.

        Returns:
            Tuple of (success, list of execution results).
        """
        group = self.get_group(name)
        if not group:
            return False, []

        results: list[ExecutionResult] = []

        def launch_app(app_name: str) -> ExecutionResult:
            return executor.execute(app_name)

        # Launch apps with optional delay
        for i, app_name in enumerate(group.apps):
            if i > 0 and group.delay > 0:
                # Small delay between launches
                import time

                time.sleep(group.delay)

            result = launch_app(app_name)
            results.append(result)

        success = all(r.success for r in results)
        return success, results

    def launch_group_parallel(
        self, name: str, executor: AppExecutor
    ) -> tuple[bool, list[ExecutionResult]]:
        """
        Launch all apps in a group in parallel.

        Args:
            name: Group name.
            executor: App executor instance.

        Returns:
            Tuple of (success, list of execution results).
        """
        group = self.get_group(name)
        if not group:
            return False, []

        with ThreadPoolExecutor(max_workers=len(group.apps)) as pool:
            results = list(pool.map(executor.execute, group.apps))

        success = all(r.success for r in results)
        return success, results

    def update_group(
        self,
        name: str,
        apps: Optional[list[str]] = None,
        description: Optional[str] = None,
        delay: Optional[float] = None,
    ) -> bool:
        """
        Update an existing group.

        Args:
            name: Group name to update.
            apps: New app list (optional).
            description: New description (optional).
            delay: New delay (optional).

        Returns:
            True if updated successfully.
        """
        name = name.lower().strip()
        if name not in self.groups:
            return False

        group = self.groups[name]

        # Don't allow updating default groups
        if group in self.DEFAULT_GROUPS:
            # Create a new custom group based on the default
            new_group = AppGroup(
                name=group.name,
                apps=apps or group.apps,
                description=description or group.description,
                delay=delay if delay is not None else group.delay,
            )
            self.groups[name] = new_group
        else:
            if apps is not None:
                group.apps = apps
            if description is not None:
                group.description = description
            if delay is not None:
                group.delay = delay

        self._save_groups()
        return True
