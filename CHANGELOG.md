# Changelog

All notable changes to AIpp Opener will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - v0.3.0-dev

### Added
- **Setup Wizard** - Interactive first-time configuration assistant
- **Logging System** - Comprehensive logging with configurable levels (DEBUG, INFO, WARNING, ERROR)
- **Log Level Configuration** - Set log level via CLI (`--log-level`) or config file
- **Enhanced Error Messages** - Better error reporting with detailed logging

### Changed
- Updated version to 0.3.0-dev
- Improved error handling in executor with detailed logging
- Enhanced configuration management with logging integration
- Better history tracking with debug information

### Improved
- Application execution now logs all steps for easier debugging
- Configuration loading/saving now logged
- History recording now includes debug information
- Platform detection now logs which detector is being used

## [0.2.0] - 2026-03-18

### Added
- **GUI Frontend** - Full-featured tkinter-based GUI with search, favorites, and settings
- **System Tray Integration** - Run AIpp Opener in the system tray for quick access
- **Keyboard Shortcuts** - Global hotkey support (Ctrl+Alt+Space by default) for quick launcher
- **App Categories** - Automatic categorization of applications (Browser, Editor, IDE, Media, etc.)
- **App Icons** - Icon detection and display support for GUI
- **Shell Completions** - Bash, Zsh, and Fish completion scripts
- **Docker/Container Support** - Containerfile and docker-compose.yml for containerized testing
- **Favorites System** - Pin frequently used apps for quick access
- **History & Predictions** - Track usage and get smart suggestions

### Changed
- Improved NLP intent extraction with better action word handling
- Enhanced fuzzy matching with category-aware suggestions
- Updated configuration to support new features

### Fixed
- Better error handling for missing dependencies
- Improved cross-platform compatibility

## [0.1.0] - 2026-03-18

### Added
- Initial release
- Natural language app launching
- Support for NixOS and Debian app detection
- Multiple AI providers (Ollama, Gemini, OpenAI, OpenRouter)
- Voice input support
- Interactive CLI mode
- Usage history tracking
- System notifications

---

## Version Summary

### 0.2.0 Features
| Feature | Description |
|---------|-------------|
| GUI | Full graphical interface with search and categories |
| Tray | System tray icon with quick menu |
| Shortcuts | Global keyboard shortcuts |
| Categories | 15+ app categories for organization |
| Icons | Application icon detection |
| Completions | Shell completions for all major shells |
| Docker | Container support for testing |

### Planned for 0.3.0
- [ ] Web search integration
- [ ] Custom command support
- [ ] App groups/workspaces
- [ ] Sync across devices
- [ ] Plugin system
