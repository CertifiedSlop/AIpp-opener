"""Configuration management for AIpp Opener."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


class AIProviderConfig(BaseModel):
    """Configuration for AI provider."""

    provider: str = Field(default="ollama", description="AI provider: ollama, gemini, openai, openrouter")
    model: str = Field(default="llama3.2", description="Model to use")
    api_key: Optional[str] = Field(default=None, description="API key (not needed for Ollama)")
    base_url: Optional[str] = Field(default=None, description="Base URL for API (for Ollama: http://localhost:11434)")
    temperature: float = Field(default=0.3, ge=0, le=1, description="Temperature for AI responses")
    log_level: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")


class AppConfig(BaseModel):
    """Main application configuration."""

    ai: AIProviderConfig = Field(default_factory=AIProviderConfig)
    voice_enabled: bool = Field(default=False, description="Enable voice input")
    notifications_enabled: bool = Field(default=True, description="Enable system notifications")
    history_enabled: bool = Field(default=True, description="Enable usage history")
    max_suggestions: int = Field(default=5, ge=1, le=10, description="Maximum number of suggestions")
    default_shell: str = Field(default="bash", description="Default shell for command execution")


class ConfigManager:
    """Manages application configuration."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "aipp_opener"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: AppConfig = self._load_or_create()
        logger.debug("ConfigManager initialized with config file: %s", self.config_file)

    def _load_or_create(self) -> AppConfig:
        """Load existing config or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                logger.info("Loaded configuration from %s", self.config_file)
                return AppConfig(**data)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Could not load config file: %s. Using defaults.", e)

        # Create default config
        logger.info("Creating default configuration at %s", self.config_file)
        config = AppConfig()
        self._save(config)
        return config

    def _save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        logger.debug("Configuration saved to %s", self.config_file)

    def save(self) -> None:
        """Save current configuration."""
        self._save(self.config)
        logger.info("Configuration saved")

    def get(self) -> AppConfig:
        """Get current configuration."""
        return self.config

    def update(self, **kwargs) -> AppConfig:
        """Update configuration with new values."""
        logger.debug("Updating configuration: %s", kwargs)
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.config.ai, key):
                setattr(self.config.ai, key, value)
        self.save()
        return self.config
