"""Enhanced AI features with context-aware suggestions and learning.

This module provides intelligent app suggestions based on:
- Time of day
- Usage patterns
- Recent activity
- Application relationships
- User context (day of week, work hours)
"""

import json
from datetime import datetime, time
from pathlib import Path
from typing import Optional
from collections import defaultdict
from dataclasses import dataclass, field

from aipp_opener.logger_config import get_logger
from aipp_opener.history import HistoryManager

logger = get_logger(__name__)


@dataclass
class TimePattern:
    """Represents a time-based usage pattern."""

    hour_ranges: list[tuple[int, int]]  # List of (start, end) hour tuples
    days_of_week: list[int]  # 0=Monday, 6=Sunday
    app_name: str
    frequency: int  # How often this pattern occurs


@dataclass
class AppRelationship:
    """Represents a relationship between two applications."""

    app_a: str
    app_b: str
    co_occurrence_count: int  # How often they're used together
    typical_order: tuple[str, str]  # Which app is usually opened first


@dataclass
class ContextState:
    """Current user context."""

    current_hour: int
    current_day: int  # 0=Monday, 6=Sunday
    is_work_hours: bool
    is_weekend: bool
    recent_apps: list[str] = field(default_factory=list)
    session_start_time: Optional[datetime] = None


class ContextAwareSuggester:
    """Provides context-aware application suggestions."""

    # Common app relationships
    COMMON_RELATIONSHIPS = {
        ("code", "terminal"): "development",
        ("firefox", "code"): "research_coding",
        ("slack", "code"): "communication_dev",
        ("spotify", "code"): "music_productivity",
        ("vlc", "firefox"): "media_browsing",
        ("libreoffice", "firefox"): "office_research",
        ("thunderbird", "libreoffice"): "office_suite",
        ("gimp", "inkscape"): "graphics_design",
        ("discord", "code"): "social_coding",
        ("steam", "discord"): "gaming_social",
    }

    # Work hours definition (9 AM - 6 PM)
    WORK_HOUR_START = 9
    WORK_HOUR_END = 18

    def __init__(
        self,
        history_manager: Optional[HistoryManager] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize the context-aware suggester.

        Args:
            history_manager: History manager for usage data.
            config_path: Path to store learned patterns.
        """
        self.history = history_manager or HistoryManager()
        
        if config_path is None:
            config_path = (
                Path.home() / ".config" / "aipp_opener" / "ai_context.json"
            )
        self.config_path = config_path

        self._time_patterns: list[TimePattern] = []
        self._app_relationships: list[AppRelationship] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load learned patterns from config."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self._time_patterns = [
                        TimePattern(**p) for p in data.get("time_patterns", [])
                    ]
                    self._app_relationships = [
                        AppRelationship(**r) for r in data.get("app_relationships", [])
                    ]
                logger.debug(
                    "Loaded %d time patterns and %d relationships",
                    len(self._time_patterns),
                    len(self._app_relationships),
                )
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Could not load AI context patterns: %s", e)

    def _save_patterns(self) -> None:
        """Save learned patterns to config."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "time_patterns": [
                {
                    "hour_ranges": p.hour_ranges,
                    "days_of_week": p.days_of_week,
                    "app_name": p.app_name,
                    "frequency": p.frequency,
                }
                for p in self._time_patterns
            ],
            "app_relationships": [
                {
                    "app_a": r.app_a,
                    "app_b": r.app_b,
                    "co_occurrence_count": r.co_occurrence_count,
                    "typical_order": r.typical_order,
                }
                for r in self._app_relationships
            ],
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_current_context(self) -> ContextState:
        """Get the current user context."""
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()  # 0=Monday

        is_work_hours = (
            self.WORK_HOUR_START <= current_hour < self.WORK_HOUR_END
        )
        is_weekend = current_day >= 5

        # Get recent apps from history
        recent = self.history.get_recent(limit=5)
        recent_apps = [entry["app_name"] for entry in recent]

        return ContextState(
            current_hour=current_hour,
            current_day=current_day,
            is_work_hours=is_work_hours,
            is_weekend=is_weekend,
            recent_apps=recent_apps,
            session_start_time=now,
        )

    def get_suggestions(
        self,
        partial_input: str = "",
        limit: int = 5,
        context: Optional[ContextState] = None,
    ) -> list[dict]:
        """
        Get context-aware app suggestions.

        Args:
            partial_input: Optional partial user input.
            limit: Maximum number of suggestions.
            context: Optional context state (uses current if None).

        Returns:
            List of suggestion dicts with app_name, score, and reason.
        """
        if context is None:
            context = self.get_current_context()

        suggestions: dict[str, dict] = {}

        # Get base predictions from history
        base_predictions = self.history.get_predictions(partial_input, limit=limit * 2)

        # Score each prediction
        for app_name in base_predictions:
            score = 1.0
            reasons = []

            # Time-based scoring
            time_score, time_reason = self._score_by_time(app_name, context)
            score += time_score
            if time_reason:
                reasons.append(time_reason)

            # Pattern-based scoring
            pattern_score, pattern_reason = self._score_by_patterns(
                app_name, context
            )
            score += pattern_score
            if pattern_reason:
                reasons.append(pattern_reason)

            # Relationship-based scoring
            rel_score, rel_reason = self._score_by_relationships(
                app_name, context
            )
            score += rel_score
            if rel_reason:
                reasons.append(rel_reason)

            suggestions[app_name] = {
                "app_name": app_name,
                "score": score,
                "reasons": reasons,
            }

        # Sort by score and return top results
        sorted_suggestions = sorted(
            suggestions.values(), key=lambda x: x["score"], reverse=True
        )

        return sorted_suggestions[:limit]

    def _score_by_time(
        self, app_name: str, context: ContextState
    ) -> tuple[float, Optional[str]]:
        """Score an app based on time of day."""
        score = 0.0
        reason = None

        # Check learned time patterns
        for pattern in self._time_patterns:
            if pattern.app_name != app_name:
                continue

            # Check if current time matches pattern
            hour_matches = any(
                start <= context.current_hour < end
                for start, end in pattern.hour_ranges
            )
            day_matches = (
                not pattern.days_of_week
                or context.current_day in pattern.days_of_week
            )

            if hour_matches and day_matches:
                score += 2.0
                reason = f"Usually used at this time (pattern: {pattern.frequency}x)"
                break

        # General heuristics
        if context.is_work_hours and not context.is_weekend:
            # Work-related apps get a boost
            work_apps = {
                "code",
                "terminal",
                "libreoffice",
                "thunderbird",
                "slack",
                "zoom",
                "teams",
            }
            if app_name.lower() in work_apps:
                score += 0.5
                if not reason:
                    reason = "Commonly used during work hours"

        return score, reason

    def _score_by_patterns(
        self, app_name: str, context: ContextState
    ) -> tuple[float, Optional[str]]:
        """Score an app based on learned usage patterns."""
        score = 0.0
        reason = None

        # Check if this app is frequently used on this day
        frequent_apps = self.history.get_frequent_apps(limit=20)
        for app_info in frequent_apps:
            if app_info["app_name"] == app_name:
                # Base score from frequency
                score += min(app_info["count"] / 10, 2.0)
                reason = f"Frequently used ({app_info['count']} times)"
                break

        return score, reason

    def _score_by_relationships(
        self, app_name: str, context: ContextState
    ) -> tuple[float, Optional[str]]:
        """Score an app based on relationships with recently used apps."""
        score = 0.0
        reason = None

        if not context.recent_apps:
            return score, reason

        # Check learned relationships
        for rel in self._app_relationships:
            if rel.app_a == app_name and rel.app_b in context.recent_apps:
                score += 1.5
                reason = f"Often used with {rel.app_b}"
                break
            if rel.app_b == app_name and rel.app_a in context.recent_apps:
                score += 1.5
                reason = f"Often used with {rel.app_a}"
                break

        # Check common relationships
        for (app_a, app_b), _ in self.COMMON_RELATIONSHIPS.items():
            if app_a == app_name and app_b in context.recent_apps:
                score += 1.0
                if not reason:
                    reason = f"Commonly paired with {app_b}"
            if app_b == app_name and app_a in context.recent_apps:
                score += 1.0
                if not reason:
                    reason = f"Commonly paired with {app_a}"

        return score, reason

    def learn_from_usage(
        self, user_input: str, app_name: str, context: Optional[ContextState] = None
    ) -> None:
        """
        Learn from a usage event.

        Args:
            user_input: The user's input.
            app_name: The app that was opened.
            context: Optional context state (uses current if None).
        """
        if context is None:
            context = self.get_current_context()

        # Update time patterns
        self._update_time_patterns(app_name, context)

        # Update app relationships
        if context.recent_apps:
            for recent_app in context.recent_apps:
                self._update_relationship(recent_app, app_name)

        # Save learned patterns
        self._save_patterns()

        logger.debug("Learned from usage: %s -> %s", user_input, app_name)

    def _update_time_patterns(self, app_name: str, context: ContextState) -> None:
        """Update time-based patterns for an app."""
        # Find existing pattern
        for pattern in self._time_patterns:
            if pattern.app_name == app_name:
                pattern.frequency += 1
                return

        # Create new pattern
        new_pattern = TimePattern(
            hour_ranges=[(context.current_hour, context.current_hour + 1)],
            days_of_week=[context.current_day],
            app_name=app_name,
            frequency=1,
        )
        self._time_patterns.append(new_pattern)

    def _update_relationship(self, app_a: str, app_b: str) -> None:
        """Update relationship between two apps."""
        # Normalize order
        if app_a > app_b:
            app_a, app_b = app_b, app_a

        # Find existing relationship
        for rel in self._app_relationships:
            if rel.app_a == app_a and rel.app_b == app_b:
                rel.co_occurrence_count += 1
                return

        # Create new relationship
        new_rel = AppRelationship(
            app_a=app_a,
            app_b=app_b,
            co_occurrence_count=1,
            typical_order=(app_a, app_b),
        )
        self._app_relationships.append(new_rel)

    def clear_learning(self) -> None:
        """Clear all learned patterns."""
        self._time_patterns = []
        self._app_relationships = []
        self._save_patterns()
        logger.info("Cleared all learned AI patterns")

    def get_learning_stats(self) -> dict:
        """Get statistics about learned patterns."""
        return {
            "time_patterns": len(self._time_patterns),
            "app_relationships": len(self._app_relationships),
            "total_patterns": len(self._time_patterns)
            + len(self._app_relationships),
        }
