"""Async application detector base class for AIpp Opener."""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class AppInfo:
    """Information about a detected application."""

    name: str
    executable: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[list[str]] = None
    icon: Optional[str] = None


class AsyncAppDetector(ABC):
    """Abstract base class for async application detectors."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this detector is available on the current system."""
        pass

    @abstractmethod
    async def detect(self) -> list[AppInfo]:
        """Detect applications on the system."""
        pass

    @abstractmethod
    async def refresh(self) -> None:
        """Refresh the detection cache."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return detector name."""
        pass
