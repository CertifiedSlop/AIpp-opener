"""Google Gemini AI provider."""

import os
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from aipp_opener.ai.base import AIProvider, AIResponse


class GeminiProvider(AIProvider):
    """AI provider using Google Gemini."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-pro",
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self._client = None
    
    @property
    def name(self) -> str:
        return "gemini"
    
    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        if not GEMINI_AVAILABLE:
            return False
        return self.api_key is not None and len(self.api_key) > 0
    
    def _get_client(self):
        """Get or create the Gemini client."""
        if self._client is None and self.api_key:
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client
    
    def chat(self, messages: list[dict], **kwargs) -> AIResponse:
        """Send a chat request to Gemini."""
        if not self.is_available():
            raise RuntimeError("Gemini provider is not configured")
        
        client = self._get_client()
        if client is None:
            raise RuntimeError("Failed to initialize Gemini client")
        
        temperature = kwargs.get("temperature", 0.3)
        
        # Convert messages to Gemini format
        # Gemini expects a simple string or alternating user/model messages
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # Gemini doesn't have system messages, prepend to prompt
                prompt = f"{content}\n\n{prompt}"
            elif role == "user":
                prompt = f"{prompt}{content}\n"
            elif role == "assistant":
                prompt = f"{prompt}Assistant: {content}\n"
        
        # Generate response
        response = client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature
            )
        )
        
        return AIResponse(
            text=response.text,
            model=self.model,
            raw_response={"text": response.text}
        )
