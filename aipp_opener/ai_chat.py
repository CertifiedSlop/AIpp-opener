"""Enhanced AI chat integration with context awareness.

This module provides intelligent chat-based app recommendations
using AI providers with context-aware suggestions.
"""

import asyncio
from typing import Optional, TYPE_CHECKING

from aipp_opener.logger_config import get_logger
from aipp_opener.context_aware_suggester import ContextAwareSuggester, ContextState

if TYPE_CHECKING:
    from aipp_opener.ai.base import AIProvider

logger = get_logger(__name__)


class AIChatAssistant:
    """AI-powered chat assistant for app recommendations."""

    SYSTEM_PROMPT = """You are an intelligent application launcher assistant for Linux.
Your role is to help users find and open applications based on their natural language requests.

Guidelines:
- Be concise and direct
- Suggest the most relevant application for the user's request
- If multiple apps could work, suggest the most popular one first
- Consider the user's context (time of day, recent activity)
- If no app matches, suggest searching the web or installing the app
- Format responses as JSON with: {"app_name": "...", "confidence": 0.0-1.0, "reason": "..."}

Available application categories:
- Browsers: firefox, chrome, chromium, brave
- Development: code, sublime-text, vim, nvim, emacs, terminal
- Communication: slack, discord, telegram-desktop, signal-desktop, thunderbird
- Media: vlc, mpv, spotify, rhythmbox
- Office: libreoffice, writer, calc, impress, evolution
- Graphics: gimp, inkscape, eog, krita, blender
- System: settings, nautilus, dolphin, thunar

If the user's request doesn't match any app, respond with:
{"app_name": null, "confidence": 0.0, "reason": "No matching app found"}
"""

    def __init__(
        self,
        ai_provider: "AIProvider",
        suggester: Optional[ContextAwareSuggester] = None,
    ):
        """
        Initialize the AI chat assistant.

        Args:
            ai_provider: AI provider for chat completions.
            suggester: Context-aware suggester for additional insights.
        """
        self.ai_provider = ai_provider
        self.suggester = suggester or ContextAwareSuggester()
        self._conversation_history: list[dict] = []

    def _build_messages(
        self,
        user_input: str,
        context: Optional[ContextState] = None,
        available_apps: Optional[list[dict]] = None,
    ) -> list[dict]:
        """Build the message list for the AI chat."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # Add context information
        if context:
            context_info = self._format_context(context)
            messages.append(
                {"role": "system", "content": f"Current context: {context_info}"}
            )

        # Add available apps
        if available_apps:
            apps_info = self._format_available_apps(available_apps)
            messages.append(
                {"role": "system", "content": f"Available apps: {apps_info}"}
            )

        # Add conversation history (last 5 messages)
        messages.extend(self._conversation_history[-5:])

        # Add user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def _format_context(self, context: ContextState) -> str:
        """Format context state for the AI."""
        parts = []

        parts.append(f"Time: {context.current_hour:02d}:00")
        parts.append(
            "Day: "
            + [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ][context.current_day]
        )
        parts.append(f"Work hours: {'Yes' if context.is_work_hours else 'No'}")
        parts.append(f"Weekend: {'Yes' if context.is_weekend else 'No'}")

        if context.recent_apps:
            parts.append(f"Recent apps: {', '.join(context.recent_apps[-3:])}")

        return "; ".join(parts)

    def _format_available_apps(self, apps: list[dict]) -> str:
        """Format available apps list for the AI."""
        formatted = []
        for app in apps[:20]:  # Limit to 20 apps
            name = app.get("name", app.get("app_name", ""))
            categories = app.get("categories", [])
            if categories:
                formatted.append(f"{name} ({', '.join(categories[:2])})")
            else:
                formatted.append(name)

        return ", ".join(formatted)

    async def chat(
        self,
        user_input: str,
        context: Optional[ContextState] = None,
        available_apps: Optional[list[dict]] = None,
    ) -> dict:
        """
        Chat with the AI assistant to get app recommendation.

        Args:
            user_input: User's natural language request.
            context: Optional context state.
            available_apps: Optional list of available apps.

        Returns:
            Dict with app_name, confidence, and reason.
        """
        if context is None:
            context = self.suggester.get_current_context()

        messages = self._build_messages(user_input, context, available_apps)

        try:
            response = await self.ai_provider.chat(messages, temperature=0.3)

            # Parse the response
            result = self._parse_ai_response(response.text)

            # Enhance with context-aware suggestions if AI didn't find a match
            if result.get("app_name") is None:
                context_suggestions = self.suggester.get_suggestions(
                    partial_input=user_input, limit=3, context=context
                )
                if context_suggestions:
                    result["fallback_suggestions"] = [
                        s["app_name"] for s in context_suggestions
                    ]
                    result["reason"] = (
                        result.get("reason", "")
                        + " Context suggestions: "
                        + ", ".join(result["fallback_suggestions"])
                    )

            # Update conversation history
            self._conversation_history.append(
                {"role": "user", "content": user_input}
            )
            self._conversation_history.append(
                {"role": "assistant", "content": str(result)}
            )

            # Learn from this interaction if an app was selected
            if result.get("app_name"):
                self.suggester.learn_from_usage(user_input, result["app_name"], context)

            return result

        except Exception as e:
            logger.error("AI chat error: %s", e)
            # Fallback to context-aware suggestions
            suggestions = self.suggester.get_suggestions(
                partial_input=user_input, limit=3, context=context
            )
            return {
                "app_name": suggestions[0]["app_name"] if suggestions else None,
                "confidence": 0.5,
                "reason": f"AI unavailable, using context suggestions: {[s['app_name'] for s in suggestions]}",
                "fallback_suggestions": [s["app_name"] for s in suggestions],
            }

    def _parse_ai_response(self, response_text: str) -> dict:
        """Parse the AI's JSON response."""
        import json

        try:
            # Try to extract JSON from the response
            # The AI might include extra text, so we look for JSON blocks
            text = response_text.strip()

            # Try direct parsing first
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

            # Look for JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse AI response: %s", e)

        # Default response
        return {
            "app_name": None,
            "confidence": 0.0,
            "reason": "Failed to parse AI response",
        }

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation_history = []
        logger.debug("Cleared AI chat conversation history")

    def get_context_suggestions(
        self, limit: int = 5
    ) -> list[dict]:
        """
        Get pure context-aware suggestions (without AI).

        Args:
            limit: Maximum number of suggestions.

        Returns:
            List of suggestion dicts.
        """
        context = self.suggester.get_current_context()
        return self.suggester.get_suggestions(limit=limit, context=context)


class SyncAIChatAssistant:
    """Synchronous wrapper for AIChatAssistant."""

    def __init__(
        self,
        ai_provider: "AIProvider",
        suggester: Optional[ContextAwareSuggester] = None,
    ):
        """
        Initialize the synchronous AI chat assistant.

        Args:
            ai_provider: AI provider for chat completions.
            suggester: Context-aware suggester for additional insights.
        """
        self.async_assistant = AIChatAssistant(ai_provider, suggester)

    def chat(
        self,
        user_input: str,
        context: Optional[dict] = None,
        available_apps: Optional[list[dict]] = None,
    ) -> dict:
        """
        Chat with the AI assistant (synchronous).

        Args:
            user_input: User's natural language request.
            context: Optional context state as dict.
            available_apps: Optional list of available apps.

        Returns:
            Dict with app_name, confidence, and reason.
        """
        return asyncio.run(
            self.async_assistant.chat(user_input, None, available_apps)
        )

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.async_assistant.clear_history()

    def get_context_suggestions(self, limit: int = 5) -> list[dict]:
        """Get context-aware suggestions."""
        return asyncio.run(self.async_assistant.get_context_suggestions(limit))
