"""App categories and filtering module."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AppCategory(Enum):
    """Application categories."""
    BROWSER = "browser"
    EDITOR = "editor"
    IDE = "ide"
    TERMINAL = "terminal"
    MEDIA = "media"
    VIDEO = "video"
    AUDIO = "audio"
    GRAPHICS = "graphics"
    OFFICE = "office"
    COMMUNICATION = "communication"
    GAME = "game"
    SYSTEM = "system"
    UTILITY = "utility"
    DEVELOPMENT = "development"
    OTHER = "other"


# Category mappings for common applications
APP_CATEGORY_MAP = {
    # Browsers
    "firefox": AppCategory.BROWSER,
    "chrome": AppCategory.BROWSER,
    "chromium": AppCategory.BROWSER,
    "brave": AppCategory.BROWSER,
    "opera": AppCategory.BROWSER,
    "vivaldi": AppCategory.BROWSER,
    "epiphany": AppCategory.BROWSER,
    "midori": AppCategory.BROWSER,

    # Text Editors
    "gedit": AppCategory.EDITOR,
    "kate": AppCategory.EDITOR,
    "mousepad": AppCategory.EDITOR,
    "xed": AppCategory.EDITOR,
    "pluma": AppCategory.EDITOR,
    "leafpad": AppCategory.EDITOR,
    "vim": AppCategory.EDITOR,
    "nvim": AppCategory.EDITOR,
    "emacs": AppCategory.EDITOR,
    "nano": AppCategory.EDITOR,
    "micro": AppCategory.EDITOR,

    # IDEs
    "code": AppCategory.IDE,
    "code-insiders": AppCategory.IDE,
    "pycharm": AppCategory.IDE,
    "intellij": AppCategory.IDE,
    "webstorm": AppCategory.IDE,
    "phpstorm": AppCategory.IDE,
    "goland": AppCategory.IDE,
    "rustrover": AppCategory.IDE,
    "eclipse": AppCategory.IDE,
    "netbeans": AppCategory.IDE,
    "atom": AppCategory.IDE,
    "sublime-text": AppCategory.IDE,
    "cursor": AppCategory.IDE,

    # Terminals
    "gnome-terminal": AppCategory.TERMINAL,
    "konsole": AppCategory.TERMINAL,
    "alacritty": AppCategory.TERMINAL,
    "kitty": AppCategory.TERMINAL,
    "wezterm": AppCategory.TERMINAL,
    "foot": AppCategory.TERMINAL,
    "urxvt": AppCategory.TERMINAL,
    "st": AppCategory.TERMINAL,
    "terminator": AppCategory.TERMINAL,
    "tilix": AppCategory.TERMINAL,
    "guake": AppCategory.TERMINAL,
    "yakuake": AppCategory.TERMINAL,

    # Media Players
    "vlc": AppCategory.MEDIA,
    "mpv": AppCategory.MEDIA,
    "mplayer": AppCategory.MEDIA,
    "smplayer": AppCategory.MEDIA,
    "celluloid": AppCategory.MEDIA,
    "dragon": AppCategory.MEDIA,
    "totem": AppCategory.MEDIA,

    # Video Editors
    "kdenlive": AppCategory.VIDEO,
    "openshot": AppCategory.VIDEO,
    "shotcut": AppCategory.VIDEO,
    "olive": AppCategory.VIDEO,
    "pitivi": AppCategory.VIDEO,
    "flowblade": AppCategory.VIDEO,

    # Audio Players
    "rhythmbox": AppCategory.AUDIO,
    "audacious": AppCategory.AUDIO,
    "clementine": AppCategory.AUDIO,
    "amarok": AppCategory.AUDIO,
    "quodlibet": AppCategory.AUDIO,
    "sayonara": AppCategory.AUDIO,
    "spotify": AppCategory.AUDIO,
    "ncspot": AppCategory.AUDIO,

    # Audio Editors
    "audacity": AppCategory.AUDIO,
    "ardour": AppCategory.AUDIO,
    "reaper": AppCategory.AUDIO,

    # Graphics
    "gimp": AppCategory.GRAPHICS,
    "inkscape": AppCategory.GRAPHICS,
    "krita": AppCategory.GRAPHICS,
    "kolourpaint": AppCategory.GRAPHICS,
    "pinta": AppCategory.GRAPHICS,
    "mypaint": AppCategory.GRAPHICS,
    "eog": AppCategory.GRAPHICS,
    "gwenview": AppCategory.GRAPHICS,
    "ristretto": AppCategory.GRAPHICS,
    "feh": AppCategory.GRAPHICS,
    "sxiv": AppCategory.GRAPHICS,
    "blender": AppCategory.GRAPHICS,
    "darktable": AppCategory.GRAPHICS,
    "rawtherapee": AppCategory.GRAPHICS,

    # Office
    "libreoffice": AppCategory.OFFICE,
    "writer": AppCategory.OFFICE,
    "calc": AppCategory.OFFICE,
    "impress": AppCategory.OFFICE,
    "draw": AppCategory.OFFICE,
    "math": AppCategory.OFFICE,
    "base": AppCategory.OFFICE,
    "evolution": AppCategory.OFFICE,
    "thunderbird": AppCategory.OFFICE,
    "onlyoffice": AppCategory.OFFICE,
    "wps": AppCategory.OFFICE,
    "okular": AppCategory.OFFICE,
    "evince": AppCategory.OFFICE,
    "zathura": AppCategory.OFFICE,

    # Communication
    "discord": AppCategory.COMMUNICATION,
    "slack": AppCategory.COMMUNICATION,
    "zoom": AppCategory.COMMUNICATION,
    "teams": AppCategory.COMMUNICATION,
    "telegram-desktop": AppCategory.COMMUNICATION,
    "telegram": AppCategory.COMMUNICATION,
    "signal-desktop": AppCategory.COMMUNICATION,
    "signal": AppCategory.COMMUNICATION,
    "whatsapp-desktop": AppCategory.COMMUNICATION,
    "whatsapp": AppCategory.COMMUNICATION,
    "skype": AppCategory.COMMUNICATION,
    "element": AppCategory.COMMUNICATION,
    "matrix": AppCategory.COMMUNICATION,
    "hexchat": AppCategory.COMMUNICATION,
    "weechat": AppCategory.COMMUNICATION,
    "pidgin": AppCategory.COMMUNICATION,

    # Games / Launchers
    "steam": AppCategory.GAME,
    "lutris": AppCategory.GAME,
    "heroic": AppCategory.GAME,
    "bottles": AppCategory.GAME,
    "playonlinux": AppCategory.GAME,
    "wine": AppCategory.GAME,
    "minecraft": AppCategory.GAME,
    "0ad": AppCategory.GAME,
    "supertuxkart": AppCategory.GAME,

    # System
    "nautilus": AppCategory.SYSTEM,
    "dolphin": AppCategory.SYSTEM,
    "thunar": AppCategory.SYSTEM,
    "pcmanfm": AppCategory.SYSTEM,
    "nemo": AppCategory.SYSTEM,
    "ranger": AppCategory.SYSTEM,
    "nnn": AppCategory.SYSTEM,
    "vifm": AppCategory.SYSTEM,
    "gnome-control-center": AppCategory.SYSTEM,
    "systemsettings": AppCategory.SYSTEM,
    "settings": AppCategory.SYSTEM,
    "gnome-tweaks": AppCategory.SYSTEM,
    "dconf-editor": AppCategory.SYSTEM,

    # Development
    "git": AppCategory.DEVELOPMENT,
    "gitk": AppCategory.DEVELOPMENT,
    "meld": AppCategory.DEVELOPMENT,
    "diffuse": AppCategory.DEVELOPMENT,
    "docker": AppCategory.DEVELOPMENT,
    "docker-desktop": AppCategory.DEVELOPMENT,
    "postman": AppCategory.DEVELOPMENT,
    "insomnia": AppCategory.DEVELOPMENT,
    "wireshark": AppCategory.DEVELOPMENT,
    "virtualbox": AppCategory.DEVELOPMENT,
    "vmware": AppCategory.DEVELOPMENT,
    "qemu": AppCategory.DEVELOPMENT,
    "android-studio": AppCategory.DEVELOPMENT,
    "mysql-workbench": AppCategory.DEVELOPMENT,
    "pgadmin": AppCategory.DEVELOPMENT,
    "dbeaver": AppCategory.DEVELOPMENT,

    # Utilities
    "calculator": AppCategory.UTILITY,
    "gnome-calculator": AppCategory.UTILITY,
    "kcalc": AppCategory.UTILITY,
    "archive-manager": AppCategory.UTILITY,
    "file-roller": AppCategory.UTILITY,
    "baobab": AppCategory.UTILITY,
    "gnome-disk-utility": AppCategory.UTILITY,
    "gparted": AppCategory.UTILITY,
    "timeshift": AppCategory.UTILITY,
    "bleachbit": AppCategory.UTILITY,
    "stacer": AppCategory.UTILITY,
    "htop": AppCategory.UTILITY,
    "btop": AppCategory.UTILITY,
    "glances": AppCategory.UTILITY,
    "obs": AppCategory.UTILITY,
    "obs-studio": AppCategory.UTILITY,
    "simple-scan": AppCategory.UTILITY,
    "transmission": AppCategory.UTILITY,
    "qbittorrent": AppCategory.UTILITY,
    "deluge": AppCategory.UTILITY,
}

# Category keywords for desktop file matching
CATEGORY_KEYWORDS = {
    AppCategory.BROWSER: ["web", "browser", "internet", "www"],
    AppCategory.EDITOR: ["text", "editor", "word"],
    AppCategory.IDE: ["ide", "development", "programming", "coding"],
    AppCategory.TERMINAL: ["terminal", "console", "shell"],
    AppCategory.MEDIA: ["media", "player", "multimedia"],
    AppCategory.VIDEO: ["video", "movie", "film"],
    AppCategory.AUDIO: ["audio", "music", "sound"],
    AppCategory.GRAPHICS: ["graphics", "image", "photo", "drawing", "3d"],
    AppCategory.OFFICE: ["office", "document", "spreadsheet", "presentation", "pdf"],
    AppCategory.COMMUNICATION: ["chat", "message", "communication", "social"],
    AppCategory.GAME: ["game", "gaming"],
    AppCategory.SYSTEM: ["system", "settings", "file", "manager"],
    AppCategory.DEVELOPMENT: ["development", "debug", "database", "network"],
    AppCategory.UTILITY: ["utility", "tool", "utility", "accessory"],
}


@dataclass
class CategorizedApp:
    """Application with category information."""
    name: str
    executable: str
    display_name: str
    category: AppCategory
    description: Optional[str] = None
    keywords: Optional[list[str]] = None


class AppCategorizer:
    """Categorizes applications based on name and metadata."""

    def __init__(self):
        self.category_map = APP_CATEGORY_MAP.copy()

    def categorize(self, name: str, desktop_categories: Optional[list[str]] = None) -> AppCategory:
        """
        Categorize an application.

        Args:
            name: Application name.
            desktop_categories: Categories from .desktop file.

        Returns:
            AppCategory for the application.
        """
        name_lower = name.lower()

        # Check direct mapping first
        if name_lower in self.category_map:
            return self.category_map[name_lower]

        # Check partial matches
        for app_name, category in self.category_map.items():
            if app_name in name_lower or name_lower in app_name:
                return category

        # Try to categorize from desktop categories
        if desktop_categories:
            return self._categorize_from_desktop(desktop_categories)

        # Check keywords in name
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return AppCategory.OTHER

    def _categorize_from_desktop(self, categories: list[str]) -> AppCategory:
        """Categorize from desktop file categories."""
        category_map = {
            "AudioVideo": AppCategory.MEDIA,
            "Audio": AppCategory.AUDIO,
            "Video": AppCategory.VIDEO,
            "Graphics": AppCategory.GRAPHICS,
            "Network": AppCategory.COMMUNICATION,
            "Office": AppCategory.OFFICE,
            "Development": AppCategory.DEVELOPMENT,
            "Education": AppCategory.UTILITY,
            "Game": AppCategory.GAME,
            "Settings": AppCategory.SYSTEM,
            "System": AppCategory.SYSTEM,
            "Utility": AppCategory.UTILITY,
            "FileTools": AppCategory.UTILITY,
        }

        for cat in categories:
            if cat in category_map:
                return category_map[cat]

        return AppCategory.OTHER

    def filter_by_category(
        self,
        apps: list,
        category: AppCategory
    ) -> list:
        """
        Filter apps by category.

        Args:
            apps: List of AppInfo objects.
            category: Category to filter by.

        Returns:
            List of apps in the specified category.
        """
        result = []
        for app in apps:
            app_category = self.categorize(app.name, app.categories)
            if app_category == category:
                result.append(app)
        return result

    def get_category_counts(self, apps: list) -> dict[AppCategory, int]:
        """
        Get count of apps per category.

        Args:
            apps: List of AppInfo objects.

        Returns:
            Dict mapping categories to counts.
        """
        counts = dict.fromkeys(AppCategory, 0)

        for app in apps:
            category = self.categorize(app.name, app.categories)
            counts[category] += 1

        return counts

    def get_categories_summary(self, apps: list) -> list[dict]:
        """
        Get summary of apps by category.

        Args:
            apps: List of AppInfo objects.

        Returns:
            List of dicts with category info.
        """
        counts = self.get_category_counts(apps)

        result = []
        for category, count in counts.items():
            if count > 0:
                result.append({
                    "category": category.value,
                    "display_name": category.value.title(),
                    "count": count,
                })

        # Sort by count descending
        result.sort(key=lambda x: x["count"], reverse=True)
        return result
