"""OpenAI API provider."""

import os
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from aipp_opener.ai.base import AIProvider, AIResponse


class OpenAIProvider(AIProvider):
    """AI provider using OpenAI API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self._client = None
    
    @property
    def name(self) -> str:
        return "openai"
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        if not OPENAI_AVAILABLE:
            return False
        return self.api_key is not None and len(self.api_key) > 0
    
    def _get_client(self) -> "OpenAI":
        """Get or create the OpenAI client."""
        if self._client is None:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client
    
    def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to OpenAI."""
        if not self.is_available():
            raise RuntimeError("OpenAI provider is not configured")
        
        client = self._get_client()
        temperature = kwargs.get("temperature", 0.3)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
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
