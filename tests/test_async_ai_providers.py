"""Tests for async AI providers (Phase 6C)."""

import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Import at module level
from aipp_opener.async_ai_providers import AsyncOllamaProvider, AsyncGeminiProvider, AsyncOpenAIProvider


class TestAsyncOllamaProvider(unittest.TestCase):
    """Tests for async Ollama provider."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_ai_providers import AsyncOllamaProvider
        self.provider = AsyncOllamaProvider(model="llama3.2", base_url="http://localhost:11434")

    def test_name_property(self):
        """Test provider name property."""
        self.assertEqual(self.provider.name, "ollama")

    def test_init_default_values(self):
        """Test initialization with default values."""
        provider = AsyncOllamaProvider()
        self.assertEqual(provider.model, "llama3.2")
        self.assertEqual(provider.base_url, "http://localhost:11434")
        self.assertEqual(provider.timeout, 60)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        provider = AsyncOllamaProvider(model="mistral", base_url="http://custom:11434", timeout=30)
        self.assertEqual(provider.model, "mistral")
        self.assertEqual(provider.base_url, "http://custom:11434")
        self.assertEqual(provider.timeout, 30)

    def test_is_available_success(self):
        """Test availability check when Ollama is running."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [{"name": "llama3.2:latest"}, {"name": "mistral:7b"}]
            })
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                result = await self.provider.is_available()
                self.assertTrue(result)

        asyncio.run(run_test())

    def test_is_available_model_not_found(self):
        """Test availability check when model is not found."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [{"name": "mistral:7b"}]
            })
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                result = await self.provider.is_available()
                self.assertFalse(result)

        asyncio.run(run_test())

    def test_chat_success(self):
        """Test successful chat request."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "message": {"content": "Hello! How can I help?"},
                "prompt_eval_count": 10,
                "eval_count": 20,
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Hello"}]
                response = await self.provider.chat(messages)

                self.assertEqual(response.text, "Hello! How can I help?")
                self.assertEqual(response.model, "llama3.2")
                self.assertEqual(response.usage["prompt_tokens"], 10)
                self.assertEqual(response.usage["completion_tokens"], 20)

        asyncio.run(run_test())

    def test_chat_with_temperature(self):
        """Test chat request with custom temperature."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "message": {"content": "Response"},
                "prompt_eval_count": 5,
                "eval_count": 10,
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Test"}]
                await self.provider.chat(messages, temperature=0.8)

                call_args = mock_session.post.call_args
                payload = call_args[1]["json"]
                self.assertEqual(payload["options"]["temperature"], 0.8)

        asyncio.run(run_test())

    def test_list_models_success(self):
        """Test listing available models."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [
                    {"name": "llama3.2:latest"},
                    {"name": "mistral:7b"},
                ]
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                models = await self.provider.list_models()
                self.assertEqual(len(models), 2)

        asyncio.run(run_test())


class TestAsyncGeminiProvider(unittest.TestCase):
    """Tests for async Gemini provider."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_ai_providers import AsyncGeminiProvider
        self.provider = AsyncGeminiProvider(api_key="test-key", model="gemini-pro")

    def test_name_property(self):
        """Test provider name property."""
        self.assertEqual(self.provider.name, "gemini")

    def test_init_default_values(self):
        """Test initialization with default values."""
        provider = AsyncGeminiProvider(api_key="key")
        self.assertEqual(provider.model, "gemini-pro")
        self.assertEqual(provider.timeout, 60)

    def test_is_available_success(self):
        """Test availability when API is accessible."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                result = await self.provider.is_available()
                self.assertTrue(result)

        asyncio.run(run_test())

    def test_is_available_failure(self):
        """Test availability when API is not accessible."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                result = await self.provider.is_available()
                self.assertFalse(result)

        asyncio.run(run_test())

    def test_chat_success(self):
        """Test successful chat request."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "candidates": [{
                    "content": {"parts": [{"text": "Hello from Gemini!"}]}
                }],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 20,
                }
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Hello"}]
                response = await self.provider.chat(messages)

                self.assertEqual(response.text, "Hello from Gemini!")
                self.assertEqual(response.model, "gemini-pro")
                self.assertEqual(response.usage["prompt_tokens"], 10)
                self.assertEqual(response.usage["completion_tokens"], 20)

        asyncio.run(run_test())

    def test_chat_with_temperature(self):
        """Test chat with custom temperature."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "candidates": [{
                    "content": {"parts": [{"text": "Response"}]}
                }],
                "usageMetadata": {}
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Test"}]
                await self.provider.chat(messages, temperature=0.7)

                call_args = mock_session.post.call_args
                payload = call_args[1]["json"]
                self.assertEqual(payload["generationConfig"]["temperature"], 0.7)

        asyncio.run(run_test())


class TestAsyncOpenAIProvider(unittest.TestCase):
    """Tests for async OpenAI provider."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.async_ai_providers import AsyncOpenAIProvider
        self.provider = AsyncOpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")

    def test_name_property(self):
        """Test provider name property."""
        self.assertEqual(self.provider.name, "openai")

    def test_init_default_values(self):
        """Test initialization with default values."""
        provider = AsyncOpenAIProvider(api_key="key")
        self.assertEqual(provider.model, "gpt-3.5-turbo")
        self.assertEqual(provider.base_url, "https://api.openai.com/v1")
        self.assertEqual(provider.timeout, 60)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        provider = AsyncOpenAIProvider(
            api_key="custom-key",
            model="gpt-4",
            base_url="https://custom.api.com",
            timeout=30
        )
        self.assertEqual(provider.api_key, "custom-key")
        self.assertEqual(provider.model, "gpt-4")
        self.assertEqual(provider.base_url, "https://custom.api.com")
        self.assertEqual(provider.timeout, 30)

    def test_is_available_success(self):
        """Test availability when API is accessible."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                result = await self.provider.is_available()
                self.assertTrue(result)

        asyncio.run(run_test())

    def test_chat_success(self):
        """Test successful chat request."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {"content": "Hello from OpenAI!"}
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                }
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Hello"}]
                response = await self.provider.chat(messages)

                self.assertEqual(response.text, "Hello from OpenAI!")
                self.assertEqual(response.model, "gpt-3.5-turbo")
                self.assertEqual(response.usage["prompt_tokens"], 10)
                self.assertEqual(response.usage["completion_tokens"], 20)

        asyncio.run(run_test())

    def test_chat_with_temperature(self):
        """Test chat with custom temperature."""
        async def run_test():
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Response"}}],
                "usage": {}
            })
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_response)

            with patch.object(self.provider, '_get_session', return_value=mock_session):
                messages = [{"role": "user", "content": "Test"}]
                await self.provider.chat(messages, temperature=0.8)

                call_args = mock_session.post.call_args
                payload = call_args[1]["json"]
                self.assertEqual(payload["temperature"], 0.8)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
