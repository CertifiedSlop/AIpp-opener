"""NLP utilities for natural language processing."""

from fuzzywuzzy import fuzz, process
from typing import Optional


class NLPProcessor:
    """Natural language processing utilities for app matching."""

    def __init__(self, threshold: int = 60):
        """
        Initialize the NLP processor.

        Args:
            threshold: Minimum fuzzy match score (0-100).
        """
        self.threshold = threshold

    def extract_app_intent(self, user_input: str) -> str:
        """
        Extract the application name/intent from user input.

        Args:
            user_input: The user's natural language command.

        Returns:
            The extracted application name or keyword.
        """
        user_input = user_input.strip().lower()

        # Common action verbs to remove
        action_words = [
            "open",
            "launch",
            "start",
            "run",
            "execute",
            "show",
            "bring up",
            "fire up",
            "kick off",
            "activate",
            "please",
            "can you",
            "could you",
            "would you",
            "i want to",
            "i need to",
            "let me",
            "let's",
        ]

        # Remove action words
        result = user_input
        for action in action_words:
            result = result.replace(action, " ")

        # Clean up extra spaces
        result = " ".join(result.split())

        # If we have multiple words, try to identify the main app name
        words = result.split()
        if len(words) > 1:
            # Look for common app patterns
            app_patterns = [
                "code",
                "studio",
                "editor",
                "terminal",
                "browser",
                "player",
                "viewer",
                "manager",
                "settings",
                "config",
            ]
            for pattern in app_patterns:
                if pattern in words:
                    # Return the phrase including the pattern
                    idx = words.index(pattern)
                    if idx > 0:
                        return " ".join(words[idx - 1 : idx + 1])
                    return " ".join(words[: idx + 1])

        return result if result else user_input

    def find_best_match(
        self, query: str, candidates: list[str], limit: int = 1
    ) -> list[tuple[str, int]]:
        """
        Find the best fuzzy matches for a query.

        Args:
            query: The search query.
            candidates: List of candidate strings to match against.
            limit: Maximum number of results to return.

        Returns:
            List of (candidate, score) tuples.
        """
        query_lower = query.lower()

        # First try exact substring match
        exact_matches = []
        for candidate in candidates:
            candidate_lower = candidate.lower()
            if query_lower in candidate_lower or candidate_lower in query_lower:
                exact_matches.append((candidate, 100))

        if exact_matches:
            return exact_matches[:limit]

        # Use fuzzy matching
        matches = process.extract(query, candidates, scorer=fuzz.WRatio, limit=limit)

        # Filter by threshold
        filtered = [(m[0], m[1]) for m in matches if m[1] >= self.threshold]
        return filtered

    def find_all_matches(
        self, query: str, candidates: list[str], min_score: Optional[int] = None
    ) -> list[tuple[str, int]]:
        """
        Find all matches above a threshold.

        Args:
            query: The search query.
            candidates: List of candidate strings to match against.
            min_score: Minimum score threshold (overrides default).

        Returns:
            List of (candidate, score) tuples.
        """
        threshold = min_score if min_score is not None else self.threshold
        query_lower = query.lower()

        matches = []

        # Check for exact/partial matches first
        for candidate in candidates:
            candidate_lower = candidate.lower()
            if query_lower == candidate_lower:
                matches.append((candidate, 100))
            elif query_lower in candidate_lower:
                matches.append((candidate, 95))
            elif candidate_lower in query_lower:
                matches.append((candidate, 90))

        if matches:
            return matches

        # Use fuzzy matching
        all_matches = process.extract(query, candidates, scorer=fuzz.WRatio, limit=len(candidates))

        return [(m[0], m[1]) for m in all_matches if m[1] >= threshold]

    def categorize_request(self, user_input: str) -> str:
        """
        Categorize the type of request.

        Args:
            user_input: The user's input.

        Returns:
            Category string: 'open', 'search', 'suggest', 'unknown'
        """
        user_input = user_input.lower()

        open_keywords = ["open", "launch", "start", "run", "execute", "show"]
        search_keywords = ["find", "search", "look for", "where is"]
        suggest_keywords = ["suggest", "recommend", "what", "which", "browse"]

        if any(kw in user_input for kw in open_keywords):
            return "open"
        elif any(kw in user_input for kw in search_keywords):
            return "search"
        elif any(kw in user_input for kw in suggest_keywords):
            return "suggest"

        return "open"  # Default to open

    def normalize_app_name(self, name: str) -> str:
        """
        Normalize an application name for matching.

        Args:
            name: The application name.

        Returns:
            Normalized name.
        """
        # Common normalizations
        normalizations = {
            "vs code": "code",
            "visual studio code": "code",
            "google chrome": "chrome",
            "firefox browser": "firefox",
            "libreoffice writer": "writer",
            "libreoffice calc": "calc",
            "libreoffice impress": "impress",
            "gimp": "gimp",
            "inkscape": "inkscape",
            "vlc media player": "vlc",
            "spotify": "spotify",
            "discord": "discord",
            "slack": "slack",
            "zoom": "zoom",
            "obs studio": "obs",
            "blender": "blender",
            "steam": "steam",
            "minecraft": "minecraft",
        }

        name_lower = name.lower().strip()
        return normalizations.get(name_lower, name_lower)
