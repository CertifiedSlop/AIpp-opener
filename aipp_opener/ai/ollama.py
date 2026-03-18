"""Ollama AI provider for local inference."""

import requests
from typing import Optional

from aipp_opener.ai.base import AIProvider, AIResponse


class OllamaProvider(AIProvider):
    """AI provider using Ollama for local inference."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False

            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            return self.model in model_names or any(self.model in name for name in model_names)
        except (requests.RequestException, ValueError):
            return False

    def chat(self, messages: list[dict], **kwargs) -> AIResponse:
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

        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
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

    def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except (requests.RequestException, ValueError):
            return []
