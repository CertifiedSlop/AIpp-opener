"""Base class for application detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppInfo:
    """Information about an installed application."""
    
    name: str
    executable: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[list[str]] = None
    
    def __post_init__(self):
        if self.display_name is None:
            self.display_name = self.name
        if self.categories is None:
            self.categories = []


class AppDetector(ABC):
    """Abstract base class for application detectors."""
    
    @abstractmethod
    def detect(self) -> list[AppInfo]:
        """
        Detect installed applications on the system.
        
        Returns:
            List of AppInfo objects representing installed applications.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this detector is available on the current system.
        
        Returns:
            True if the detector can be used on this system.
        """
        pass
    
    def get_app_by_executable(self, executable: str) -> Optional[AppInfo]:
        """
        Find an application by its executable name.
        
        Args:
            executable: The executable name to search for.
            
        Returns:
            AppInfo if found, None otherwise.
        """
        apps = self.detect()
        for app in apps:
            if app.executable.lower() == executable.lower():
                return app
        return None
    
    def get_apps_by_name(self, name: str) -> list[AppInfo]:
        """
        Find applications by name (partial match).
        
        Args:
            name: The name or partial name to search for.
            
        Returns:
            List of matching AppInfo objects.
        """
        apps = self.detect()
        name_lower = name.lower()
        return [app for app in apps if name_lower in app.name.lower() or name_lower in app.display_name.lower()]
