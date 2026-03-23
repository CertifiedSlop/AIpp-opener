"""Async AI providers for AIpp Opener.

Provides async implementations for all AI providers using aiohttp.
"""

import asyncio
import aiohttp
from typing import Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """Response from an AI provider."""

    text: str
    model: str
    usage: dict[str, int]
    raw_response: Any = None


class AsyncAIProvider(ABC):
    """Abstract base class for async AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available."""
        pass

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request."""
        pass


class AsyncOllamaProvider(AsyncAIProvider):
    """Async AI provider using Ollama for local inference."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        return "ollama"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]

                return self.model in model_names or any(
                    self.model in name for name in model_names
                )
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return False

    async def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to Ollama."""
        temperature = kwargs.get("temperature", 0.3)
        stream = kwargs.get("stream", False)

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            },
        }

        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as response:
            response.raise_for_status()
            data = await response.json()

        message = data.get("message", {})
        content = message.get("content", "")

        return AIResponse(
            text=content,
            model=self.model,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            raw_response=data,
        )

    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return []


class AsyncGeminiProvider(AsyncAIProvider):
    """Async AI provider using Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        return "gemini"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def is_available(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            session = await self._get_session()
            # Simple check by listing models
            url = f"{self.base_url}/models?key={self.api_key}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to Gemini."""
        temperature = kwargs.get("temperature", 0.3)

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
            else:
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})

        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
            },
        }

        session = await self._get_session()
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        async with session.post(
            url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as response:
            response.raise_for_status()
            data = await response.json()

        # Extract response text
        candidates = data.get("candidates", [])
        text = ""
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        # Extract token usage
        usage_metadata = data.get("usageMetadata", {})
        usage = {
            "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
            "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
        }

        return AIResponse(
            text=text,
            model=self.model,
            usage=usage,
            raw_response=data,
        )


class AsyncOpenAIProvider(AsyncAIProvider):
    """Async AI provider using OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        return "openai"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to OpenAI."""
        temperature = kwargs.get("temperature", 0.3)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json()

        choices = data.get("choices", [])
        text = ""
        if choices:
            message = choices[0].get("message", {})
            text = message.get("content", "")

        usage = data.get("usage", {})

        return AIResponse(
            text=text,
            model=self.model,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw_response=data,
        )


class AsyncOpenRouterProvider(AsyncAIProvider):
    """Async AI provider using OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/llama-3-8b-instruct",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def name(self) -> str:
        return "openrouter"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/CertifiedSlop/AIpp-opener",
                }
            )
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def is_available(self) -> bool:
        """Check if OpenRouter API is accessible."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to OpenRouter."""
        temperature = kwargs.get("temperature", 0.3)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json()

        choices = data.get("choices", [])
        text = ""
        if choices:
            message = choices[0].get("message", {})
            text = message.get("content", "")

        usage = data.get("usage", {})

        return AIResponse(
            text=text,
            model=self.model,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw_response=data,
        )
