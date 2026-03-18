"""AI provider modules for AIpp Opener."""

from aipp_opener.ai.base import AIProvider
from aipp_opener.ai.gemini import GeminiProvider
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.ai.ollama import OllamaProvider
from aipp_opener.ai.openai import OpenAIProvider
from aipp_opener.ai.openrouter import OpenRouterProvider

__all__ = [
    "AIProvider",
    "OllamaProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "NLPProcessor",
]
