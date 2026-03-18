"""Usage history and prediction module for AIpp Opener."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import Counter

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


class HistoryManager:
    """Manages usage history and provides predictions."""

    DEFAULT_HISTORY_DIR = Path.home() / ".local" / "state" / "aipp_opener"
    DEFAULT_HISTORY_FILE = DEFAULT_HISTORY_DIR / "history.json"

    def __init__(self, history_file: Optional[Path] = None, max_history: int = 1000):
        """
        Initialize the history manager.

        Args:
            history_file: Path to history file.
            max_history: Maximum number of history entries to keep.
        """
        self.history_file = history_file or self.DEFAULT_HISTORY_FILE
        self.max_history = max_history
        self._history: list[dict] = []
        logger.debug("HistoryManager initialized (file=%s, max=%d)", self.history_file, max_history)
        self._load()

    def _load(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    self._history = json.load(f)
                logger.debug("Loaded %d history entries from %s", len(self._history), self.history_file)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Could not load history file: %s", e)
                self._history = []
        else:
            logger.debug("History file does not exist: %s", self.history_file)
            self._history = []

    def _save(self) -> None:
        """Save history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(self._history, f, indent=2)
        logger.debug("Saved %d history entries to %s", len(self._history), self.history_file)

    def record(
        self,
        user_input: str,
        app_name: str,
        executable: str,
        success: bool = True
    ) -> None:
        """
        Record an app launch in history.

        Args:
            user_input: The user's original input.
            app_name: The application name.
            executable: The executable path.
            success: Whether the launch was successful.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "app_name": app_name,
            "executable": executable,
            "success": success,
        }

        self._history.append(entry)
        logger.debug("Recorded launch: %s -> %s (success=%s)", user_input, app_name, success)

        # Trim history if needed
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
            logger.debug("Trimmed history to %d entries", self.max_history)

        self._save()

    def get_frequent_apps(self, limit: int = 10) -> list[dict]:
        """
        Get frequently used applications.

        Args:
            limit: Maximum number of apps to return.

        Returns:
            List of dicts with app info and usage count.
        """
        counter = Counter(entry["app_name"] for entry in self._history if entry["success"])

        result = []
        for app_name, count in counter.most_common(limit):
            # Find the executable for this app
            executable = None
            for entry in self._history:
                if entry["app_name"] == app_name:
                    executable = entry["executable"]
                    break

            result.append({
                "app_name": app_name,
                "executable": executable,
                "count": count,
            })

        return result

    def get_predictions(self, partial_input: str, limit: int = 5) -> list[str]:
        """
        Get app predictions based on partial input.

        Args:
            partial_input: Partial user input.
            limit: Maximum number of predictions.

        Returns:
            List of predicted app names.
        """
        if not partial_input:
            # Return most frequent apps
            frequent = self.get_frequent_apps(limit)
            return [app["app_name"] for app in frequent]

        # Find history entries that match the partial input
        partial_lower = partial_input.lower()
        matches = []

        for entry in self._history:
            user_input = entry["user_input"].lower()
            app_name = entry["app_name"].lower()

            if partial_lower in user_input or partial_lower in app_name:
                matches.append((entry["app_name"], entry["success"]))

        # Sort by success and frequency
        counter = Counter(name for name, success in matches if success)
        predictions = [name for name, _ in counter.most_common(limit)]

        return predictions

    def get_recent(self, limit: int = 10) -> list[dict]:
        """
        Get recent app launches.

        Args:
            limit: Maximum number of entries.

        Returns:
            List of recent history entries.
        """
        return list(reversed(self._history[-limit:]))

    def clear(self) -> None:
        """Clear all history."""
        self._history = []
        self._save()

    def get_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dict with usage statistics.
        """
        total = len(self._history)
        successful = sum(1 for e in self._history if e["success"])

        # Most used app
        frequent = self.get_frequent_apps(1)
        most_used = frequent[0]["app_name"] if frequent else None

        return {
            "total_launches": total,
            "successful_launches": successful,
            "failed_launches": total - successful,
            "unique_apps": len(set(e["app_name"] for e in self._history)),
            "most_used_app": most_used,
        }
