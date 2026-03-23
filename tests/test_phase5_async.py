"""Tests for Phase 5 async modules and AI enhancements."""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Test async cache
class TestAsyncCache:
    """Tests for AsyncCache."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.mark.asyncio
    async def test_async_cache_set_get(self, temp_cache_dir):
        """Test setting and getting values from async cache."""
        from aipp_opener.async_cache import AsyncCache

        cache = AsyncCache("test", ttl=300, cache_dir=temp_cache_dir)
        
        # Set a value
        await cache.set("key1", "value1")
        
        # Get the value
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_async_cache_expired(self, temp_cache_dir):
        """Test that expired cache entries return None."""
        from aipp_opener.async_cache import AsyncCache

        cache = AsyncCache("test", ttl=1, cache_dir=temp_cache_dir)
        
        # Set a value with 1 second TTL
        await cache.set("key1", "value1")
        
        # Wait for expiration
        await asyncio.sleep(1.5)
        
        # Should return None
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_cache_delete(self, temp_cache_dir):
        """Test deleting from async cache."""
        from aipp_opener.async_cache import AsyncCache

        cache = AsyncCache("test", ttl=300, cache_dir=temp_cache_dir)
        
        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        
        assert result is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_async_cache_clear(self, temp_cache_dir):
        """Test clearing async cache."""
        from aipp_opener.async_cache import AsyncCache

        cache = AsyncCache("test", ttl=300, cache_dir=temp_cache_dir)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_async_cache_stats(self, temp_cache_dir):
        """Test getting cache statistics."""
        from aipp_opener.async_cache import AsyncCache

        cache = AsyncCache("test", ttl=300, cache_dir=temp_cache_dir)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        stats = await cache.stats()
        
        assert stats["name"] == "test"
        assert stats["total_entries"] == 2
        assert stats["ttl"] == 300


# Test async history
class TestAsyncHistoryManager:
    """Tests for AsyncHistoryManager."""

    @pytest.fixture
    def temp_history_file(self, tmp_path):
        """Create a temporary history file."""
        history_file = tmp_path / "history.json"
        return history_file

    @pytest.mark.asyncio
    async def test_async_history_record(self, temp_history_file):
        """Test recording history entries."""
        from aipp_opener.async_history import AsyncHistoryManager

        history = AsyncHistoryManager(history_file=temp_history_file)
        
        await history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        
        recent = await history.get_recent(limit=1)
        assert len(recent) == 1
        assert recent[0]["app_name"] == "firefox"

    @pytest.mark.asyncio
    async def test_async_history_predictions(self, temp_history_file):
        """Test getting predictions from async history."""
        from aipp_opener.async_history import AsyncHistoryManager

        history = AsyncHistoryManager(history_file=temp_history_file)
        
        # Record some entries
        await history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        await history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        await history.record("open code", "code", "/usr/bin/code", success=True)
        
        predictions = await history.get_predictions("fire", limit=5)
        assert "firefox" in predictions

    @pytest.mark.asyncio
    async def test_async_history_frequent_apps(self, temp_history_file):
        """Test getting frequent apps."""
        from aipp_opener.async_history import AsyncHistoryManager

        history = AsyncHistoryManager(history_file=temp_history_file)
        
        for _ in range(5):
            await history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        for _ in range(3):
            await history.record("open code", "code", "/usr/bin/code", success=True)
        
        frequent = await history.get_frequent_apps(limit=5)
        
        assert frequent[0]["app_name"] == "firefox"
        assert frequent[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_async_history_stats(self, temp_history_file):
        """Test getting history statistics."""
        from aipp_opener.async_history import AsyncHistoryManager

        history = AsyncHistoryManager(history_file=temp_history_file)
        
        await history.record("open firefox", "firefox", "/usr/bin/firefox", success=True)
        await history.record("open code", "code", "/usr/bin/code", success=False)
        
        stats = await history.get_stats()
        
        assert stats["total_launches"] == 2
        assert stats["successful_launches"] == 1
        assert stats["failed_launches"] == 1


# Test async web search
class TestAsyncWebSearcher:
    """Tests for AsyncWebSearcher."""

    def test_async_web_searcher_init(self):
        """Test AsyncWebSearcher initialization."""
        from aipp_opener.async_web_search import AsyncWebSearcher

        searcher = AsyncWebSearcher()
        
        assert searcher.default_engine == "google"
        assert "google" in searcher.get_available_engines()
        assert "duckduckgo" in searcher.get_available_engines()

    def test_async_web_searcher_search_url(self):
        """Test generating search URLs."""
        from aipp_opener.async_web_search import AsyncWebSearcher

        searcher = AsyncWebSearcher()
        
        url = searcher.search("test query", open_browser=False)
        assert "google.com" in url
        assert "test+query" in url or "test%20query" in url

    def test_async_web_searcher_custom_engine(self, tmp_path):
        """Test adding custom search engines."""
        from aipp_opener.async_web_search import AsyncWebSearcher

        config_path = tmp_path / "search_engines.json"
        searcher = AsyncWebSearcher(config_path=config_path)
        
        result = searcher.add_custom_engine(
            "nixpkgs",
            "https://search.nixos.org/packages?query={query}",
            "NixOS Packages"
        )
        
        assert result is True
        assert "nixpkgs" in searcher.get_available_engines()

    @pytest.mark.asyncio
    async def test_async_search_multiple(self):
        """Test searching multiple engines."""
        from aipp_opener.async_web_search import AsyncWebSearcher

        searcher = AsyncWebSearcher()
        
        results = await searcher.search_multiple("test", engines=["google", "duckduckgo"])
        
        assert len(results) == 2
        assert all("search_url" in r for r in results)


# Test context-aware suggester
class TestContextAwareSuggester:
    """Tests for ContextAwareSuggester."""

    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Create a temporary config file."""
        return tmp_path / "ai_context.json"

    def test_get_current_context(self, temp_config_path):
        """Test getting current context."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester

        suggester = ContextAwareSuggester(config_path=temp_config_path)
        context = suggester.get_current_context()
        
        assert context.current_hour == datetime.now().hour
        assert context.current_day == datetime.now().weekday()
        assert isinstance(context.is_work_hours, bool)
        assert isinstance(context.is_weekend, bool)

    def test_get_suggestions(self, temp_config_path):
        """Test getting suggestions."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester, ContextState

        suggester = ContextAwareSuggester(config_path=temp_config_path)
        
        context = ContextState(
            current_hour=10,
            current_day=0,
            is_work_hours=True,
            is_weekend=False,
            recent_apps=["firefox"],
        )
        
        suggestions = suggester.get_suggestions(limit=5, context=context)
        
        # Should return suggestions even with empty history
        assert isinstance(suggestions, list)

    def test_learn_from_usage(self, temp_config_path):
        """Test learning from usage."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester, ContextState

        suggester = ContextAwareSuggester(config_path=temp_config_path)
        
        context = ContextState(
            current_hour=10,
            current_day=0,
            is_work_hours=True,
            is_weekend=False,
            recent_apps=["firefox"],
        )
        
        suggester.learn_from_usage("open code", "code", context)
        
        stats = suggester.get_learning_stats()
        assert stats["time_patterns"] >= 1

    def test_clear_learning(self, temp_config_path):
        """Test clearing learned patterns."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester, ContextState

        suggester = ContextAwareSuggester(config_path=temp_config_path)
        
        context = ContextState(
            current_hour=10,
            current_day=0,
            is_work_hours=True,
            is_weekend=False,
            recent_apps=[],
        )
        
        suggester.learn_from_usage("open code", "code", context)
        suggester.clear_learning()
        
        stats = suggester.get_learning_stats()
        assert stats["total_patterns"] == 0


# Test async executor
class TestAsyncAppExecutor:
    """Tests for AsyncAppExecutor."""

    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        """Test executing non-existent application."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor(use_notifications=False)
        
        result = await executor.execute("nonexistent_app_xyz123")
        
        assert result.success is False
        assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor(use_notifications=False)
        
        # Use a command that should exist
        result = await executor.execute("echo", args=["hello"], background=False)
        
        assert result.success is True
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_retry(self):
        """Test execution with retry logic."""
        from aipp_opener.async_executor import AsyncAppExecutor

        executor = AsyncAppExecutor(use_notifications=False)
        
        result = await executor.execute_with_retry(
            "nonexistent_app",
            max_retries=2,
            retry_delay=0.1
        )
        
        assert result.success is False


# Test AI chat assistant (mocked)
class TestAIChatAssistant:
    """Tests for AIChatAssistant."""

    def test_parse_ai_response_valid_json(self):
        """Test parsing valid JSON response."""
        from aipp_opener.ai_chat import AIChatAssistant
        from unittest.mock import Mock

        mock_provider = Mock()
        assistant = AIChatAssistant(mock_provider)
        
        response = '{"app_name": "firefox", "confidence": 0.9, "reason": "Browser request"}'
        result = assistant._parse_ai_response(response)
        
        assert result["app_name"] == "firefox"
        assert result["confidence"] == 0.9

    def test_parse_ai_response_with_extra_text(self):
        """Test parsing JSON embedded in text."""
        from aipp_opener.ai_chat import AIChatAssistant
        from unittest.mock import Mock

        mock_provider = Mock()
        assistant = AIChatAssistant(mock_provider)
        
        response = 'Sure! Here\'s the app: {"app_name": "code", "confidence": 0.8, "reason": "IDE"}'
        result = assistant._parse_ai_response(response)
        
        assert result["app_name"] == "code"

    def test_parse_ai_response_invalid(self):
        """Test parsing invalid response."""
        from aipp_opener.ai_chat import AIChatAssistant
        from unittest.mock import Mock

        mock_provider = Mock()
        assistant = AIChatAssistant(mock_provider)
        
        response = "I don't understand"
        result = assistant._parse_ai_response(response)
        
        assert result["app_name"] is None
        assert result["confidence"] == 0.0

    def test_format_context(self):
        """Test formatting context for AI."""
        from aipp_opener.ai_chat import AIChatAssistant, ContextState
        from unittest.mock import Mock

        mock_provider = Mock()
        assistant = AIChatAssistant(mock_provider)
        
        context = ContextState(
            current_hour=14,
            current_day=1,
            is_work_hours=True,
            is_weekend=False,
            recent_apps=["firefox", "code"],
        )
        
        formatted = assistant._format_context(context)
        
        assert "14:00" in formatted
        assert "Tuesday" in formatted
        assert "Work hours: Yes" in formatted
        assert "firefox" in formatted


# Test async AI providers (mocked)
class TestAsyncAIProviders:
    """Tests for async AI providers."""

    @pytest.mark.asyncio
    async def test_async_ollama_provider_init(self):
        """Test AsyncOllamaProvider initialization."""
        from aipp_opener.async_ai_providers import AsyncOllamaProvider

        provider = AsyncOllamaProvider(model="llama3.2")
        
        assert provider.name == "ollama"
        assert provider.model == "llama3.2"

    @pytest.mark.asyncio
    async def test_async_ollama_is_available_fail(self):
        """Test AsyncOllamaProvider availability check (should fail without server)."""
        from aipp_opener.async_ai_providers import AsyncOllamaProvider

        provider = AsyncOllamaProvider()
        
        # Should return False when Ollama is not running
        available = await provider.is_available()
        assert available is False

    def test_async_provider_properties(self):
        """Test async provider properties."""
        from aipp_opener.async_ai_providers import (
            AsyncOllamaProvider,
            AsyncOpenAIProvider,
            AsyncGeminiProvider,
            AsyncOpenRouterProvider,
        )

        ollama = AsyncOllamaProvider()
        assert ollama.name == "ollama"

        openai = AsyncOpenAIProvider(api_key="test")
        assert openai.name == "openai"

        gemini = AsyncGeminiProvider(api_key="test")
        assert gemini.name == "gemini"

        openrouter = AsyncOpenRouterProvider(api_key="test")
        assert openrouter.name == "openrouter"


# Integration tests
class TestPhase5Integration:
    """Integration tests for Phase 5 features."""

    def test_async_cache_and_history_integration(self, tmp_path):
        """Test async cache and history working together."""
        from aipp_opener.async_cache import AsyncCache
        from aipp_opener.async_history import AsyncHistoryManager

        async def run_test():
            cache_dir = tmp_path / "cache"
            cache_dir.mkdir()
            
            cache = AsyncCache("test", ttl=300, cache_dir=cache_dir)
            history = AsyncHistoryManager(history_file=tmp_path / "history.json")
            
            # Cache some data
            await cache.set("apps", ["firefox", "code"])
            
            # Record in history
            await history.record("open firefox", "firefox", "/usr/bin/firefox")
            
            # Verify both work
            cached = await cache.get("apps")
            recent = await history.get_recent(limit=1)
            
            return cached, recent

        cached, recent = asyncio.run(run_test())
        
        assert cached == ["firefox", "code"]
        assert len(recent) == 1

    def test_context_suggester_with_history(self, tmp_path):
        """Test context suggester integrated with history."""
        from aipp_opener.context_aware_suggester import ContextAwareSuggester
        from aipp_opener.history import HistoryManager

        history_file = tmp_path / "history.json"
        config_path = tmp_path / "ai_context.json"
        
        history = HistoryManager(history_file=history_file)
        suggester = ContextAwareSuggester(
            history_manager=history,
            config_path=config_path
        )
        
        # Record some usage
        history.record("open firefox", "firefox", "/usr/bin/firefox")
        history.record("open code", "code", "/usr/bin/code")
        
        # Get suggestions
        suggestions = suggester.get_suggestions(limit=5)
        
        assert isinstance(suggestions, list)
