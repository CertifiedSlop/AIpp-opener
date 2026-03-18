"""Base class for AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    """Response from an AI provider."""

    text: str
    model: str
    usage: Optional[dict] = None
    raw_response: Optional[dict] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.

        Returns:
            True if the provider can be used.
        """
        pass

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """
        Send a chat request to the AI provider.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            **kwargs: Additional provider-specific arguments.

        Returns:
            AIResponse with the model's response.
        """
        pass

    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Complete a prompt using the AI provider.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            **kwargs: Additional provider-specific arguments.

        Returns:
            The model's response text.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.chat(messages, **kwargs)
        return response.text

    def extract_app_name(self, user_input: str) -> str:
        """
        Extract the application name from user input using AI.

        Args:
            user_input: The user's natural language command.

        Returns:
            The extracted application name.
        """
        system_prompt = """You are an assistant that extracts application names from user commands.
Respond with ONLY the application name, nothing else.

Examples:
- "open firefox" -> firefox
- "launch vs code" -> code
- "start google chrome" -> google-chrome
- "run terminal" -> terminal
- "open the browser" -> browser
"""

        response = self.complete(user_input, system_prompt=system_prompt)
        return response.strip().lower()

    def suggest_apps(self, user_input: str, available_apps: list[str], max_suggestions: int = 5) -> list[str]:
        """
        Suggest applications based on user input.

        Args:
            user_input: The user's request.
            available_apps: List of available application names.
            max_suggestions: Maximum number of suggestions.

        Returns:
            List of suggested application names.
        """
        apps_list = ", ".join(available_apps[:20])  # Limit context

        system_prompt = f"""You are an assistant that suggests applications based on user requests.
Available applications: {apps_list}

Given a user request, suggest the most relevant applications from the available list.
Respond with ONLY a comma-separated list of application names, nothing else.
Suggest up to {max_suggestions} applications.
"""

        response = self.complete(user_input, system_prompt=system_prompt)
        suggestions = [s.strip().lower() for s in response.split(",")]
        return [s for s in suggestions if s][:max_suggestions]
