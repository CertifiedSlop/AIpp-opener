"""Extended tests for AI modules to improve coverage."""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGeminiProviderExtended(unittest.TestCase):
    """Extended tests for Gemini provider."""

    def test_gemini_not_available_without_key(self):
        """Test Gemini is not available without API key."""
        with patch('aipp_opener.ai.gemini.GEMINI_AVAILABLE', False):
            from aipp_opener.ai.gemini import GeminiProvider
            provider = GeminiProvider()
            self.assertFalse(provider.is_available())

    def test_gemini_not_available_no_library(self):
        """Test Gemini is not available without library."""
        with patch('aipp_opener.ai.gemini.GEMINI_AVAILABLE', False):
            from aipp_opener.ai.gemini import GeminiProvider
            provider = GeminiProvider(api_key="test")
            self.assertFalse(provider.is_available())

    def test_gemini_chat_without_api_key(self):
        """Test Gemini chat fails without API key."""
        from aipp_opener.ai.gemini import GeminiProvider
        provider = GeminiProvider()
        
        with self.assertRaises(RuntimeError):
            provider.chat([{"role": "user", "content": "test"}])

    def test_gemini_chat_without_client(self):
        """Test Gemini chat fails without initialized client."""
        with patch('aipp_opener.ai.gemini.GEMINI_AVAILABLE', True):
            from aipp_opener.ai.gemini import GeminiProvider
            provider = GeminiProvider(api_key="test")
            
            with patch.object(provider, '_get_client', return_value=None):
                with self.assertRaises(RuntimeError):
                    provider.chat([{"role": "user", "content": "test"}])

    def test_gemini_chat_with_system_message(self):
        """Test Gemini chat handles system messages."""
        mock_genai = MagicMock()
        mock_genai.types.GenerationConfig = MagicMock()

        with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
            with patch('aipp_opener.ai.gemini.GEMINI_AVAILABLE', True):
                from aipp_opener.ai.gemini import GeminiProvider

                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Response"
                mock_client.generate_content.return_value = mock_response

                provider = GeminiProvider(api_key="test")
                with patch.object(provider, '_get_client', return_value=mock_client):
                    messages = [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "Hello"}
                    ]
                    response = provider.chat(messages)
                    self.assertEqual(response.text, "Response")

    def test_gemini_chat_with_assistant_message(self):
        """Test Gemini chat handles assistant messages."""
        mock_genai = MagicMock()
        mock_genai.types.GenerationConfig = MagicMock()

        with patch.dict('sys.modules', {'google.generativeai': mock_genai}):
            with patch('aipp_opener.ai.gemini.GEMINI_AVAILABLE', True):
                from aipp_opener.ai.gemini import GeminiProvider

                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Response"
                mock_client.generate_content.return_value = mock_response

                provider = GeminiProvider(api_key="test")
                with patch.object(provider, '_get_client', return_value=mock_client):
                    messages = [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there"}
                    ]
                    response = provider.chat(messages)
                    self.assertEqual(response.text, "Response")


class TestOpenAIProviderExtended(unittest.TestCase):
    """Extended tests for OpenAI provider."""

    def test_openai_not_available_without_key(self):
        """Test OpenAI is not available without API key."""
        with patch('aipp_opener.ai.openai.OPENAI_AVAILABLE', False):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider()
            self.assertFalse(provider.is_available())

    def test_openai_not_available_no_library(self):
        """Test OpenAI is not available without library."""
        with patch('aipp_opener.ai.openai.OPENAI_AVAILABLE', False):
            from aipp_opener.ai.openai import OpenAIProvider
            provider = OpenAIProvider(api_key="test")
            self.assertFalse(provider.is_available())

    def test_openai_chat_without_api_key(self):
        """Test OpenAI chat fails without API key."""
        from aipp_opener.ai.openai import OpenAIProvider
        provider = OpenAIProvider()
        
        with self.assertRaises(RuntimeError):
            provider.chat([{"role": "user", "content": "test"}])

    def test_openai_chat_with_empty_content(self):
        """Test OpenAI chat handles empty content."""
        with patch('aipp_opener.ai.openai.OPENAI_AVAILABLE', True):
            from aipp_opener.ai.openai import OpenAIProvider
            
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = None
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response
            
            provider = OpenAIProvider(api_key="test")
            with patch.object(provider, '_get_client', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                response = provider.chat(messages)
                self.assertEqual(response.text, "")

    def test_openai_chat_with_base_url(self):
        """Test OpenAI chat with custom base URL."""
        with patch('aipp_opener.ai.openai.OPENAI_AVAILABLE', True):
            from aipp_opener.ai.openai import OpenAIProvider
            
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Response"
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response
            
            provider = OpenAIProvider(api_key="test", base_url="https://custom.api.com")
            with patch.object(provider, '_get_client', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                response = provider.chat(messages)
                self.assertEqual(response.text, "Response")


class TestOpenRouterProviderExtended(unittest.TestCase):
    """Extended tests for OpenRouter provider."""

    def test_openrouter_not_available_without_key(self):
        """Test OpenRouter is not available without API key."""
        with patch('aipp_opener.ai.openrouter.OPENAI_AVAILABLE', False):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider()
            self.assertFalse(provider.is_available())

    def test_openrouter_not_available_no_library(self):
        """Test OpenRouter is not available without library."""
        with patch('aipp_opener.ai.openrouter.OPENAI_AVAILABLE', False):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            provider = OpenRouterProvider(api_key="test")
            self.assertFalse(provider.is_available())

    def test_openrouter_chat_without_api_key(self):
        """Test OpenRouter chat fails without API key."""
        from aipp_opener.ai.openrouter import OpenRouterProvider
        provider = OpenRouterProvider()
        
        with self.assertRaises(RuntimeError):
            provider.chat([{"role": "user", "content": "test"}])

    def test_openrouter_chat_with_empty_content(self):
        """Test OpenRouter chat handles empty content."""
        with patch('aipp_opener.ai.openrouter.OPENAI_AVAILABLE', True):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = None
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage = None
            mock_client.chat.completions.create.return_value = mock_response
            
            provider = OpenRouterProvider(api_key="test")
            with patch.object(provider, '_get_client', return_value=mock_client):
                messages = [{"role": "user", "content": "test"}]
                response = provider.chat(messages)
                self.assertEqual(response.text, "")

    def test_openrouter_list_models_without_key(self):
        """Test OpenRouter list models without API key."""
        from aipp_opener.ai.openrouter import OpenRouterProvider
        provider = OpenRouterProvider()
        models = provider.list_available_models()
        self.assertEqual(models, [])

    def test_openrouter_list_models_error(self):
        """Test OpenRouter list models handles errors."""
        with patch('aipp_opener.ai.openrouter.OPENAI_AVAILABLE', True):
            from aipp_opener.ai.openrouter import OpenRouterProvider
            
            mock_client = MagicMock()
            mock_client.models.list.side_effect = Exception("API error")
            
            provider = OpenRouterProvider(api_key="test")
            with patch.object(provider, '_get_client', return_value=mock_client):
                models = provider.list_available_models()
                self.assertEqual(models, [])


class TestAIProviderBase(unittest.TestCase):
    """Tests for AI provider base class."""

    def test_ai_response_dataclass(self):
        """Test AIResponse dataclass."""
        from aipp_opener.ai.base import AIResponse
        
        response = AIResponse(
            text="Hello",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            raw_response={"test": "data"}
        )
        
        self.assertEqual(response.text, "Hello")
        self.assertEqual(response.model, "test-model")
        self.assertEqual(response.usage["prompt_tokens"], 10)
        self.assertEqual(response.raw_response, {"test": "data"})


if __name__ == "__main__":
    unittest.main()
