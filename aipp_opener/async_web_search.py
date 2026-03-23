"""Async web search integration for AIpp Opener.

Supports built-in engines and user-defined custom search engines.
Uses aiohttp for async HTTP requests.
"""

import json
import aiohttp
import webbrowser
import urllib.parse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class SearchEngine:
    """Represents a search engine configuration."""

    name: str
    url_template: str
    description: str = ""
    is_custom: bool = False

    def search(self, query: str) -> str:
        """Generate search URL for given query."""
        encoded_query = urllib.parse.quote_plus(query)
        return self.url_template.format(query=encoded_query)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "url_template": self.url_template,
            "description": self.description,
            "is_custom": self.is_custom,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SearchEngine":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            url_template=data.get("url_template", ""),
            description=data.get("description", ""),
            is_custom=data.get("is_custom", False),
        )


class AsyncWebSearcher:
    """Provides async web search functionality with optional result fetching.

    Supports both built-in engines and user-defined custom engines.
    Custom engines are stored in ~/.config/aipp_opener/search_engines.json
    """

    # Built-in search engines (cannot be modified)
    BUILTIN_ENGINES = {
        "google": SearchEngine(
            name="google",
            url_template="https://www.google.com/search?q={query}",
            description="Google Search",
        ),
        "duckduckgo": SearchEngine(
            name="duckduckgo",
            url_template="https://duckduckgo.com/?q={query}",
            description="DuckDuckGo Privacy Search",
        ),
        "bing": SearchEngine(
            name="bing",
            url_template="https://www.bing.com/search?q={query}",
            description="Microsoft Bing",
        ),
        "github": SearchEngine(
            name="github",
            url_template="https://github.com/search?q={query}",
            description="GitHub Code Search",
        ),
        "archwiki": SearchEngine(
            name="archwiki",
            url_template="https://wiki.archlinux.org/title={query}",
            description="Arch Linux Wiki",
        ),
        "stackoverflow": SearchEngine(
            name="stackoverflow",
            url_template="https://stackoverflow.com/search?q={query}",
            description="Stack Overflow Q&A",
        ),
        "reddit": SearchEngine(
            name="reddit",
            url_template="https://www.reddit.com/search?q={query}",
            description="Reddit Search",
        ),
    }

    def __init__(
        self,
        default_engine: str = "google",
        config_path: Optional[Path] = None,
    ):
        """
        Initialize the async web searcher.

        Args:
            default_engine: Default search engine to use.
            config_path: Path to custom engines config file.
        """
        self.default_engine = default_engine
        self._engines: dict[str, SearchEngine] = dict(self.BUILTIN_ENGINES)
        self._custom_engines: dict[str, SearchEngine] = {}

        if config_path is None:
            config_path = Path.home() / ".config" / "aipp_opener" / "search_engines.json"
        self.config_path = config_path

        self._load_custom_engines()
        self._validate_engine(default_engine)

    def _load_custom_engines(self) -> None:
        """Load custom search engines from config file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    for item in data.get("engines", []):
                        engine = SearchEngine.from_dict(item)
                        engine.is_custom = True
                        self._custom_engines[engine.name.lower()] = engine
                        self._engines[engine.name.lower()] = engine
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load custom search engines: {e}")

    def _save_custom_engines(self) -> None:
        """Save custom search engines to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "engines": [engine.to_dict() for engine in self._custom_engines.values()]
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def _validate_engine(self, engine: str) -> None:
        """Validate that the search engine is supported."""
        if engine not in self._engines:
            available = ", ".join(self.get_available_engines())
            raise ValueError(
                f"Unsupported search engine: {engine}. Available: {available}"
            )

    def search(
        self, query: str, engine: Optional[str] = None, open_browser: bool = True
    ) -> Optional[str]:
        """
        Perform a web search (synchronous, opens browser).

        Args:
            query: Search query string.
            engine: Search engine to use (uses default if None).
            open_browser: Whether to open the search in browser.

        Returns:
            The search URL if successful, None otherwise.
        """
        engine = engine or self.default_engine
        self._validate_engine(engine)

        search_engine = self._engines[engine]
        search_url = search_engine.search(query)

        if open_browser:
            webbrowser.open(search_url)

        return search_url

    async def search_async(
        self,
        query: str,
        engine: Optional[str] = None,
        fetch_results: bool = False,
        timeout: int = 10,
    ) -> dict:
        """
        Perform an async web search.

        Args:
            query: Search query string.
            engine: Search engine to use (uses default if None).
            fetch_results: Whether to fetch search results (default: just return URL).
            timeout: Request timeout in seconds.

        Returns:
            Dict with search_url and optionally html_content or error.
        """
        engine = engine or self.default_engine
        self._validate_engine(engine)

        search_engine = self._engines[engine]
        search_url = search_engine.search(query)

        result = {
            "query": query,
            "engine": engine,
            "search_url": search_url,
        }

        if fetch_results:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, timeout=timeout) as response:
                        result["status_code"] = response.status
                        result["html_content"] = await response.text()
            except aiohttp.ClientError as e:
                result["error"] = str(e)
            except asyncio.TimeoutError:
                result["error"] = "Request timed out"

        return result

    async def search_multiple(
        self,
        query: str,
        engines: Optional[list[str]] = None,
        timeout: int = 10,
    ) -> list[dict]:
        """
        Search across multiple engines concurrently.

        Args:
            query: Search query string.
            engines: List of engine names to search (uses all if None).
            timeout: Request timeout in seconds.

        Returns:
            List of search results from each engine.
        """
        if engines is None:
            engines = self.get_available_engines()

        tasks = [
            self.search_async(query, engine=eng, fetch_results=False, timeout=timeout)
            for eng in engines
        ]

        return await asyncio.gather(*tasks)

    def search_app(self, app_name: str, open_browser: bool = True) -> Optional[str]:
        """
        Search for an application on the web.

        Args:
            app_name: Name of the application to search for.
            open_browser: Whether to open the search in browser.

        Returns:
            The search URL if successful, None otherwise.
        """
        query = f"install {app_name} linux"
        return self.search(query, open_browser=open_browser)

    def search_command(self, command: str, open_browser: bool = True) -> Optional[str]:
        """
        Search for a command or how-to.

        Args:
            command: Command or task to search for.
            open_browser: Whether to open the search in browser.

        Returns:
            The search URL if successful, None otherwise.
        """
        query = f"linux command {command}"
        return self.search(query, open_browser=open_browser)

    def add_custom_engine(
        self, name: str, url_template: str, description: str = ""
    ) -> bool:
        """
        Add a custom search engine.

        Args:
            name: Unique name for the engine.
            url_template: URL template with {query} placeholder.
            description: Optional description.

        Returns:
            True if added successfully, False if name already exists.
        """
        name = name.lower().strip()

        if name in self.BUILTIN_ENGINES:
            print(f"Cannot override built-in engine: {name}")
            return False

        if name in self._custom_engines:
            print(f"Custom engine already exists: {name}")
            return False

        if "{query}" not in url_template:
            print("URL template must contain {query} placeholder")
            return False

        engine = SearchEngine(
            name=name,
            url_template=url_template,
            description=description,
            is_custom=True,
        )

        self._custom_engines[name] = engine
        self._engines[name] = engine
        self._save_custom_engines()

        return True

    def remove_custom_engine(self, name: str) -> bool:
        """
        Remove a custom search engine.

        Args:
            name: Name of the engine to remove.

        Returns:
            True if removed successfully, False if not found or built-in.
        """
        name = name.lower().strip()

        if name in self.BUILTIN_ENGINES:
            print(f"Cannot remove built-in engine: {name}")
            return False

        if name not in self._custom_engines:
            return False

        del self._custom_engines[name]
        del self._engines[name]
        self._save_custom_engines()

        return True

    def list_custom_engines(self) -> list[SearchEngine]:
        """Get list of custom search engines."""
        return list(self._custom_engines.values())

    def get_available_engines(self) -> list[str]:
        """Get list of all available engine names."""
        return list(self._engines.keys())

    def get_engine_info(self, name: str) -> Optional[SearchEngine]:
        """
        Get information about a search engine.

        Args:
            name: Engine name.

        Returns:
            SearchEngine object or None if not found.
        """
        return self._engines.get(name.lower())

    def set_default_engine(self, engine: str) -> None:
        """
        Set the default search engine.

        Args:
            engine: Search engine to set as default.

        Raises:
            ValueError: If the engine is not supported.
        """
        self._validate_engine(engine)
        self.default_engine = engine


# Import asyncio for async methods
import asyncio
