"""Tests for AI modules (Phase 6C)."""

import unittest
from unittest.mock import patch, MagicMock


class TestOllamaProvider(unittest.TestCase):
    """Tests for Ollama provider."""

    def test_name_property(self):
        """Test provider name property."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider(model="llama3.2", base_url="http://localhost:11434")
            self.assertEqual(provider.name, "ollama")

    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            self.assertEqual(provider.model, "llama3.2")
            self.assertEqual(provider.base_url, "http://localhost:11434")
            self.assertEqual(provider.timeout, 60)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider(model="mistral", base_url="http://custom:11434", timeout=30)
            self.assertEqual(provider.model, "mistral")
            self.assertEqual(provider.base_url, "http://custom:11434")
            self.assertEqual(provider.timeout, 30)

    def test_is_available_success(self):
        """Test availability check when Ollama is running."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2:latest"}, {"name": "mistral:7b"}]
        }

        with patch('aipp_opener.ai.ollama.requests.get', return_value=mock_response):
            result = provider.is_available()
            self.assertTrue(result)

    def test_is_available_model_not_found(self):
        """Test availability check when model is not found."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "mistral:7b"}]
        }

        with patch('aipp_opener.ai.ollama.requests.get', return_value=mock_response):
            result = provider.is_available()
            self.assertFalse(result)

    def test_is_available_connection_error(self):
        """Test availability check with connection error."""
        import requests

        mock_requests = MagicMock()
        mock_requests.get.side_effect = requests.RequestException("Connection error")
        mock_requests.RequestException = requests.RequestException

        with patch('aipp_opener.ai.ollama.requests', mock_requests):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            result = provider.is_available()
            self.assertFalse(result)

    def test_is_available_http_error(self):
        """Test availability check with HTTP error."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch('aipp_opener.ai.ollama.requests.get', return_value=mock_response):
            result = provider.is_available()
            self.assertFalse(result)

    def test_chat_success(self):
        """Test successful chat request."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Hello! How can I help?"},
            "prompt_eval_count": 10,
            "eval_count": 20,
        }

        with patch('aipp_opener.ai.ollama.requests.post', return_value=mock_response) as mock_post:
            messages = [{"role": "user", "content": "Hello"}]
            response = provider.chat(messages)

            self.assertEqual(response.text, "Hello! How can I help?")
            self.assertEqual(response.model, "llama3.2")
            self.assertEqual(response.usage["prompt_tokens"], 10)
            self.assertEqual(response.usage["completion_tokens"], 20)
            mock_post.assert_called_once()

    def test_chat_with_temperature(self):
        """Test chat request with custom temperature."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Response"},
            "prompt_eval_count": 5,
            "eval_count": 10,
        }

        with patch('aipp_opener.ai.ollama.requests.post', return_value=mock_response) as mock_post:
            messages = [{"role": "user", "content": "Test"}]
            provider.chat(messages, temperature=0.8)

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            self.assertEqual(payload["options"]["temperature"], 0.8)

    def test_list_models_success(self):
        """Test listing available models."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "mistral:7b"},
            ]
        }

        with patch('aipp_opener.ai.ollama.requests.get', return_value=mock_response):
            models = provider.list_models()
            self.assertEqual(len(models), 2)

    def test_list_models_empty(self):
        """Test listing models when none available."""
        with patch('aipp_opener.ai.ollama.requests'):
            from aipp_opener.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        with patch('aipp_opener.ai.ollama.requests.get', return_value=mock_response):
            models = provider.list_models()
            self.assertEqual(models, [])


class TestOpenAIProvider(unittest.TestCase):
    """Tests for OpenAI provider."""

    def test_name_property(self):
        """Test provider name property."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")
            self.assertEqual(provider.name, "openai")

    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider()
            self.assertIsNone(provider.api_key)
            self.assertEqual(provider.model, "gpt-3.5-turbo")
            self.assertIsNone(provider.base_url)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider(
                api_key="custom-key",
                model="gpt-4",
                base_url="https://custom.api.com"
            )
            self.assertEqual(provider.api_key, "custom-key")
            self.assertEqual(provider.model, "gpt-4")
            self.assertEqual(provider.base_url, "https://custom.api.com")

    def test_is_available_with_key(self):
        """Test availability when API key is provided."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            with patch('aipp_opener.ai.openai.OPENAI_AVAILABLE', True):
                from aipp_opener.ai.openai import OpenAIProvider
                provider = OpenAIProvider(api_key="key")
                result = provider.is_available()
                self.assertTrue(result)

    def test_is_available_without_key(self):
        """Test availability without API key."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider()
            result = provider.is_available()
            self.assertFalse(result)

    def test_chat_success(self):
        """Test successful chat request."""
        with patch('aipp_opener.ai.openai.OpenAI'):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider(api_key="key")
            
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from OpenAI!"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(provider, '_get_client', return_value=mock_client):
            messages = [{"role": "user", "content": "Hello"}]
            response = provider.chat(messages)

            self.assertEqual(response.text, "Hello from OpenAI!")
            self.assertEqual(response.model, "gpt-3.5-turbo")
            self.assertEqual(response.usage["prompt_tokens"], 10)
            self.assertEqual(response.usage["completion_tokens"], 20)


class TestOpenRouterProvider(unittest.TestCase):
    """Tests for OpenRouter provider."""

    def test_name_property(self):
        """Test provider name property."""
        with patch('aipp_opener.ai.openrouter.OpenAI'):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider(api_key="test-key")
            self.assertEqual(provider.name, "openrouter")

    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch('aipp_opener.ai.openrouter.OpenAI'):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider()
            self.assertIsNone(provider.api_key)
            self.assertEqual(provider.model, "meta-llama/llama-3-8b-instruct")

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with patch('aipp_opener.ai.openrouter.OpenAI'):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider(
                api_key="custom-key",
                model="anthropic/claude-3"
            )
            self.assertEqual(provider.api_key, "custom-key")
            self.assertEqual(provider.model, "anthropic/claude-3")

    def test_is_available_with_key(self):
        """Test availability when API key is provided."""
        with patch('aipp_opener.ai.openrouter.OpenAI'):
            with patch('aipp_opener.ai.openrouter.OPENAI_AVAILABLE', True):
                from aipp_opener.ai.openrouter import OpenRouterProvider
                provider = OpenRouterProvider(api_key="key")
                result = provider.is_available()
                self.assertTrue(result)

    def test_chat_success(self):
        """Test successful chat request."""
        with patch('aipp_opener.ai.openrouter.OpenAI'):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider(api_key="key")
            
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from OpenRouter!"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(provider, '_get_client', return_value=mock_client):
            messages = [{"role": "user", "content": "Hello"}]
            response = provider.chat(messages)

            self.assertEqual(response.text, "Hello from OpenRouter!")
            self.assertEqual(response.model, "meta-llama/llama-3-8b-instruct")


class TestAIChatAssistant(unittest.TestCase):
    """Tests for AI Chat Assistant."""

    def setUp(self):
        """Set up test fixtures."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester

        self.mock_provider = MagicMock()
        self.mock_provider.name = "ollama"
        self.mock_provider.chat = MagicMock()
        self.suggester = ContextAwareSuggester()
        
        from aipp_opener.ai_chat import AIChatAssistant
        self.assistant = AIChatAssistant(self.mock_provider, self.suggester)

    def test_init_with_provider(self):
        """Test initialization with provider."""
        from aipp_opener.ai_chat import AIChatAssistant
        assistant = AIChatAssistant(self.mock_provider)
        self.assertIs(assistant.ai_provider, self.mock_provider)
        self.assertIsNotNone(assistant.suggester)

    def test_build_messages_basic(self):
        """Test building basic messages."""
        messages = self.assistant._build_messages("Open firefox")
        self.assertGreater(len(messages), 0)
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "Open firefox")

    def test_build_messages_with_available_apps(self):
        """Test building messages with available apps."""
        apps = [
            {"name": "firefox", "display_name": "Firefox", "categories": ["browser"]},
        ]
        messages = self.assistant._build_messages("Open browser", available_apps=apps)
        self.assertGreater(len(messages), 2)

    def test_build_messages_includes_history(self):
        """Test that conversation history is included."""
        self.assistant._conversation_history = [
            {"role": "user", "content": "What's a good browser?"},
            {"role": "assistant", "content": "Firefox is great!"},
        ]
        messages = self.assistant._build_messages("Open firefox")
        self.assertGreater(len(messages), 2)

    def test_format_available_apps(self):
        """Test formatting available apps."""
        apps = [
            {"name": "firefox", "display_name": "Firefox", "categories": ["browser"]},
        ]
        formatted = self.assistant._format_available_apps(apps)
        self.assertIsInstance(formatted, str)

    def test_chat_basic(self):
        """Test basic chat functionality."""
        import asyncio
        from aipp_opener.ai_chat import AIChatAssistant

        mock_provider = MagicMock()
        mock_provider.name = "ollama"
        mock_response = MagicMock()
        mock_response.text = '{"app_name": "firefox", "confidence": 0.9, "reason": "Best browser"}'

        async def mock_chat(*args, **kwargs):
            return mock_response

        mock_provider.chat = mock_chat

        assistant = AIChatAssistant(mock_provider)
        result = asyncio.run(assistant.chat("Open firefox"))

        self.assertIsNotNone(result)

    def test_clear_history(self):
        """Test clearing conversation history."""
        self.assistant._conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        self.assistant.clear_history()
        self.assertEqual(len(self.assistant._conversation_history), 0)


if __name__ == "__main__":
    unittest.main()
