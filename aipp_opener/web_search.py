"""Web search integration for AIpp Opener."""

import webbrowser
import urllib.parse
from typing import Optional


class WebSearcher:
    """Provides web search functionality as fallback when apps are not found."""

    # Supported search engines
    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q={query}",
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "bing": "https://www.bing.com/search?q={query}",
        "github": "https://github.com/search?q={query}",
        "archwiki": "https://wiki.archlinux.org/title={query}",
    }

    def __init__(self, default_engine: str = "google"):
        """
        Initialize the web searcher.

        Args:
            default_engine: Default search engine to use.
        """
        self.default_engine = default_engine
        self._validate_engine(default_engine)

    def _validate_engine(self, engine: str) -> None:
        """Validate that the search engine is supported."""
        if engine not in self.SEARCH_ENGINES:
            raise ValueError(
                f"Unsupported search engine: {engine}. "
                f"Supported: {', '.join(self.SEARCH_ENGINES.keys())}"
            )

    def search(
        self, query: str, engine: Optional[str] = None, open_browser: bool = True
    ) -> Optional[str]:
        """
        Perform a web search.

        Args:
            query: Search query string.
            engine: Search engine to use (uses default if None).
            open_browser: Whether to open the search in browser.

        Returns:
            The search URL if successful, None otherwise.
        """
        engine = engine or self.default_engine
        self._validate_engine(engine)

        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query)

        # Build the search URL
        search_url = self.SEARCH_ENGINES[engine].format(query=encoded_query)

        if open_browser:
            webbrowser.open(search_url)

        return search_url

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

    def get_available_engines(self) -> list[str]:
        """Get list of available search engines."""
        return list(self.SEARCH_ENGINES.keys())

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
