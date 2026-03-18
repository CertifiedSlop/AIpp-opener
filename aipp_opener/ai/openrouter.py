"""OpenRouter AI provider for accessing multiple models."""

import os
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from aipp_opener.ai.base import AIProvider, AIResponse


class OpenRouterProvider(AIProvider):
    """AI provider using OpenRouter API for multi-model access."""
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/llama-3-8b-instruct",
    ):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self._client = None
    
    @property
    def name(self) -> str:
        return "openrouter"
    
    def is_available(self) -> bool:
        """Check if OpenRouter is configured."""
        if not OPENAI_AVAILABLE:
            return False
        return self.api_key is not None and len(self.api_key) > 0
    
    def _get_client(self) -> "OpenAI":
        """Get or create the OpenRouter client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.OPENROUTER_BASE_URL,
            )
        return self._client
    
    def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to OpenRouter."""
        if not self.is_available():
            raise RuntimeError("OpenRouter provider is not configured")
        
        client = self._get_client()
        temperature = kwargs.get("temperature", 0.3)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://github.com/aipp-opener",
                "X-Title": "AIpp Opener",
            }
        )
        
        choice = response.choices[0]
        
        return AIResponse(
            text=choice.message.content or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            raw_response=response.model_dump()
        )
    
    def list_available_models(self) -> list[str]:
        """List available models on OpenRouter."""
        if not self.is_available():
            return []
        
        try:
            client = self._get_client()
            models = client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return []
