"""Custom commands and aliases for AIpp Opener."""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CustomCommand:
    """Represents a custom command alias."""

    name: str
    command: str
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CustomCommand":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            command=data.get("command", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


class AliasManager:
    """Manages custom command aliases."""

    DEFAULT_ALIASES = [
        CustomCommand("ff", "firefox", "Open Firefox browser", ["browser", "web"]),
        CustomCommand("chrome", "google-chrome", "Open Google Chrome", ["browser", "web"]),
        CustomCommand("code", "code", "Open VS Code", ["editor", "ide"]),
        CustomCommand("vim", "vim", "Open Vim editor", ["editor", "terminal"]),
        CustomCommand("nvim", "nvim", "Open Neovim editor", ["editor", "terminal"]),
        CustomCommand("term", "gnome-terminal", "Open terminal", ["terminal"]),
        CustomCommand("files", "nautilus", "Open file manager", ["file", "manager"]),
        CustomCommand("music", "spotify", "Open Spotify", ["music", "media"]),
        CustomCommand("calc", "gnome-calculator", "Open calculator", ["utility"]),
        CustomCommand("shot", "flameshot gui", "Take screenshot", ["graphics", "utility"]),
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the alias manager.

        Args:
            config_path: Path to aliases config file.
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "aipp_opener" / "aliases.json"
        self.config_path = config_path
        self.aliases: dict[str, CustomCommand] = {}
        self._load_aliases()

    def _load_aliases(self) -> None:
        """Load aliases from config file."""
        # Start with default aliases
        for alias in self.DEFAULT_ALIASES:
            self.aliases[alias.name.lower()] = alias

        # Load user aliases (can override defaults)
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    for item in data.get("aliases", []):
                        alias = CustomCommand.from_dict(item)
                        self.aliases[alias.name.lower()] = alias
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load aliases: {e}")

    def _save_aliases(self) -> None:
        """Save user aliases to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Only save user-defined aliases (not defaults)
        user_aliases = [
            alias.to_dict()
            for alias in self.aliases.values()
            if alias not in self.DEFAULT_ALIASES
        ]

        with open(self.config_path, "w") as f:
            json.dump({"aliases": user_aliases}, f, indent=2)

    def add_alias(
        self, name: str, command: str, description: str = "", tags: Optional[list[str]] = None
    ) -> bool:
        """
        Add a new alias.

        Args:
            name: Alias name (shortcut).
            command: Command to execute.
            description: Optional description.
            tags: Optional list of tags for search.

        Returns:
            True if added successfully.
        """
        name = name.lower().strip()
        if name in self.aliases:
            return False

        alias = CustomCommand(name=name, command=command, description=description, tags=tags or [])
        self.aliases[name] = alias
        self._save_aliases()
        return True

    def remove_alias(self, name: str) -> bool:
        """
        Remove an alias.

        Args:
            name: Alias name to remove.

        Returns:
            True if removed successfully.
        """
        name = name.lower().strip()
        if name not in self.aliases:
            return False

        # Don't allow removing default aliases
        if self.aliases[name] in self.DEFAULT_ALIASES:
            return False

        del self.aliases[name]
        self._save_aliases()
        return True

    def get_alias(self, name: str) -> Optional[CustomCommand]:
        """
        Get an alias by name.

        Args:
            name: Alias name.

        Returns:
            CustomCommand if found, None otherwise.
        """
        return self.aliases.get(name.lower().strip())

    def get_command(self, name: str) -> Optional[str]:
        """
        Get the command for an alias.

        Args:
            name: Alias name.

        Returns:
            Command string if found, None otherwise.
        """
        alias = self.get_alias(name)
        return alias.command if alias else None

    def list_aliases(self) -> list[CustomCommand]:
        """Get all aliases."""
        return list(self.aliases.values())

    def search_aliases(self, query: str) -> list[CustomCommand]:
        """
        Search aliases by name, description, or tags.

        Args:
            query: Search query.

        Returns:
            List of matching aliases.
        """
        query = query.lower().strip()
        matches = []

        for alias in self.aliases.values():
            # Search in name
            if query in alias.name.lower():
                matches.append(alias)
                continue

            # Search in description
            if query in alias.description.lower():
                matches.append(alias)
                continue

            # Search in tags
            if any(query in tag.lower() for tag in alias.tags):
                matches.append(alias)
                continue

        return matches

    def update_alias(
        self,
        name: str,
        command: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """
        Update an existing alias.

        Args:
            name: Alias name to update.
            command: New command (optional).
            description: New description (optional).
            tags: New tags (optional).

        Returns:
            True if updated successfully.
        """
        name = name.lower().strip()
        if name not in self.aliases:
            return False

        alias = self.aliases[name]

        # Don't allow updating default aliases
        if alias in self.DEFAULT_ALIASES:
            # Create a new custom alias based on the default
            new_alias = CustomCommand(
                name=alias.name,
                command=command or alias.command,
                description=description or alias.description,
                tags=tags or alias.tags,
            )
            self.aliases[name] = new_alias
        else:
            if command is not None:
                alias.command = command
            if description is not None:
                alias.description = description
            if tags is not None:
                alias.tags = tags

        self._save_aliases()
        return True
