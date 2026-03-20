# AIpp Opener

**AI-powered application launcher for Linux (NixOS/Debian/Fedora/Arch)**

Open applications using natural language commands. AIpp Opener intelligently recognizes installed apps, handles variations in app names, and provides suggestions if the requested app is not found.

![Version](https://img.shields.io/badge/version-0.6.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

## ✨ Features

- 🎯 **Natural Language Interface** - Type or speak commands like "open Firefox" or "launch VS Code"
- 🖥️ **GUI Frontend** - Beautiful tkinter-based interface with search, categories, and dark/light theme
- 🤖 **AI-Powered Suggestions** - Get closest matches when app names don't exactly match
- 🎤 **Voice Input** - Open apps using voice commands
- ⌨️ **Keyboard Shortcuts** - Global hotkey (Ctrl+Alt+Space) for instant access with X11/Wayland support
- 📱 **System Tray** - Run in background with quick access menu
- 📂 **App Categories** - 15+ categories: Browser, Editor, IDE, Media, Graphics, etc.
- ⭐ **Favorites** - Pin frequently used apps for quick access
- 📝 **History & Predictions** - Remembers frequently used apps for smarter suggestions
- 🔔 **System Notifications** - Get notified when apps launch
- 🐚 **Shell Completions** - Bash, Zsh, and Fish support
- 🐳 **Docker Support** - Containerized testing with Ollama
- 🔧 **Cross-Shell Compatible** - Works in Bash, Zsh, Fish, and more
- 🌐 **Multiple AI Providers** - Ollama (local), Gemini, OpenAI, OpenRouter
- 🔌 **Plugin System** - Extend functionality with custom plugins (app detectors, commands, result modifiers)
- 🔒 **Plugin Security** - Sandboxed plugin loading with SHA256 verification and dangerous pattern detection
- 🔍 **Custom Search Engines** - Add your own search engines or use 7 built-in options
- 📁 **Recent Files** - Quick access to recently opened documents, images, code files
- 🌐 **Browser Tabs** - Detect and switch to open browser tabs (Firefox, Chrome, Chromium, Brave, Edge)
- 🎮 **App Groups** - Launch multiple apps together (dev workspace, media setup, etc.)
- 🔗 **Custom Aliases** - Define shortcuts for commonly used commands

## 📦 Installation

### Quick Install (NixOS)

```bash
# Enter development shell
nix-shell shell.nix

# Install dependencies
pip install -r requirements.txt

# Or install with all features
pip install -e ".[all]"
```

### Quick Install (Debian/Ubuntu)

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv portaudio19-dev notify-osd

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with all features
pip install -e ".[all]"
```

### Install Options

```bash
# Basic installation
pip install -e .

# With AI support
pip install -e ".[ai]"

# With GUI and tray
pip install -e ".[gui]"

# With voice support
pip install -e ".[voice]"

# With keyboard shortcuts
pip install -e ".[keyboard]"

# Everything
pip install -e ".[all]"

# With development tools
pip install -e ".[dev]"
```

### System Dependencies

```bash
# Debian/Ubuntu
sudo apt install python3-dbus python3-gi  # For Wayland plugin security

# Fedora
sudo dnf install python3-dbus python3-gobject

# Arch Linux
sudo pacman -S python-dbus python-gobject
```

### Docker/Podman

```bash
# Build the image
podman build -t aipp-opener .

# Or use docker-compose (includes Ollama)
docker compose up -d
```

## 🚀 Usage

### GUI Mode

```bash
# Open GUI interface
python -m aipp_opener --gui

# Or use the shortcut command
aipp-gui
```

### CLI Mode

```bash
# Single command
python -m aipp_opener "open firefox"
python -m aipp_opener "launch vs code"
python -m aipp_opener "start spotify"

# Interactive mode
python -m aipp_opener --interactive

# Voice mode
python -m aipp_opener --voice

# Quick launcher with keyboard shortcut
python -m aipp_opener --shortcut

# Web search fallback
python -m aipp_opener --web-search "vs code"

# Manage custom aliases
python -m aipp_opener --alias "ff=firefox"
python -m aipp_opener --list-aliases

# Launch app groups
python -m aipp_opener --group dev
python -m aipp_opener --create-group "mygroup=code,firefox,term"

# Manage plugins
python -m aipp_opener --plugins
python -m aipp_opener --enable-plugin recent_files
python -m aipp_opener --verify-plugin "myplugin=abc123..."

# Custom search engines
python -m aipp_opener --add-search-engine "nixpkgs=https://search.nixos.org/packages?query={query}"
python -m aipp_opener --list-search-engines
```

### System Tray Mode

```bash
# Run in system tray
python -m aipp_opener --tray

# Or use the shortcut command
aipp-tray
```

### Shell Integration

Add to your shell config:

```bash
# ~/.bashrc or ~/.zshrc
alias aipp='python -m aipp_opener'

# Quick launch function
app() {
    python -m aipp_opener "open $*"
}
```

```fish
# ~/.config/fish/config.fish
alias aipp 'python -m aipp_opener'

function app
    python -m aipp_opener "open $argv"
end
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+Space` | Open quick launcher |
| `Ctrl+Alt+Space` then type | Search apps |
| `Enter` | Launch selected app |
| `Escape` | Close quick launcher |

Customize the shortcut:

```bash
python -m aipp_opener --shortcut --shortcut-key "<ctrl><alt>k"
```

## 📋 Configuration

Configuration is stored in `~/.config/aipp_opener/config.json`.

### Default Configuration

```json
{
  "ai": {
    "provider": "ollama",
    "model": "llama3.2",
    "api_key": null,
    "base_url": "http://localhost:11434",
    "temperature": 0.3
  },
  "voice_enabled": false,
  "notifications_enabled": true,
  "history_enabled": true,
  "max_suggestions": 5,
  "default_shell": "bash"
}
```

### AI Provider Setup

#### Ollama (Recommended - Local)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Or a smaller model for testing
ollama pull tinyllama
```

```json
{
  "ai": {
    "provider": "ollama",
    "model": "llama3.2",
    "base_url": "http://localhost:11434"
  }
}
```

#### Google Gemini

```json
{
  "ai": {
    "provider": "gemini",
    "model": "gemini-pro",
    "api_key": "YOUR_GEMINI_API_KEY"
  }
}
```

Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

#### OpenAI

```json
{
  "ai": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "YOUR_OPENAI_API_KEY"
  }
}
```

#### OpenRouter

```json
{
  "ai": {
    "provider": "openrouter",
    "model": "meta-llama/llama-3-8b-instruct",
    "api_key": "YOUR_OPENROUTER_API_KEY"
  }
}
```

Get API key from [OpenRouter](https://openrouter.ai/).

## 🔌 Plugins

AIpp Opener supports a extensible plugin system with security features.

### Plugin Types

1. **AppDetectorPlugin** - Detect additional applications on your system
2. **CommandPlugin** - Add custom commands
3. **ResultModifierPlugin** - Modify execution results (e.g., add notifications)

### Built-in Plugins

- `custom_commands` - System utilities (update, cache clear, IP check, weather)
- `docker_detector` - Detect running Docker containers
- `notification_modifier` - Desktop notifications on app launch
- `recent_files` - GTK recent documents
- `browser_tabs` - Open browser tabs (Firefox, Chrome, Chromium, Brave, Edge)

### Plugin Management

```bash
# List all plugins
python -m aipp_opener --plugins

# Get plugin information
python -m aipp_opener --plugin-info plugin_name

# Enable/disable plugins
python -m aipp_opener --enable-plugin recent_files
python -m aipp_opener --disable-plugin docker_detector

# Security: Verify plugin integrity
python -m aipp_opener --verify-plugin "plugin_name=sha256_hash"
python -m aipp_opener --mark-plugin-verified plugin_name
python -m aipp_opener --list-unverified-plugins
```

### Plugin Security

Plugins are validated for security:
- File size limit (1MB max)
- Dangerous pattern detection (eval, exec, subprocess)
- SHA256 hash verification
- Security levels: sandboxed, restricted, trusted

See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for plugin development guide.

## 🔍 Custom Search Engines

When an app is not found, AIpp Opener can search the web. Seven search engines are built-in:

- google, duckduckgo, bing, github, archwiki, stackoverflow, reddit

Add custom search engines:

```bash
# Add NixOS package search
python -m aipp_opener --add-search-engine "nixpkgs=https://search.nixos.org/packages?query={query}"

# Add custom documentation search
python -m aipp_opener --add-search-engine "docs=https://docs.example.com/search?q={query}"

# List all engines
python -m aipp_opener --list-search-engines

# Remove custom engine
python -m aipp_opener --remove-search-engine nixpkgs
```

## 📱 App Categories

AIpp Opener automatically categorizes applications:

| Category | Examples |
|----------|----------|
| Browser | Firefox, Chrome, Chromium, Brave |
| Editor | Gedit, Kate, Vim, Emacs |
| IDE | VS Code, PyCharm, IntelliJ |
| Terminal | GNOME Terminal, Konsole, Alacritty |
| Media | VLC, MPV, Rhythmbox |
| Audio | Spotify, Audacious, Audacity |
| Graphics | GIMP, Inkscape, Krita, Blender |
| Office | LibreOffice, Thunderbird |
| Communication | Discord, Slack, Zoom, Telegram |
| Game | Steam, Lutris, Heroic |
| System | Nautilus, Dolphin, Settings |
| Development | Git, Docker, Postman |
| Utility | Calculator, Archive Manager, OBS |

## 🎯 Examples

### Natural Language Commands

```
# All of these open Firefox:
> open firefox
> launch firefox
> start firefox
> run firefox
> please open firefox
> i want to open firefox
> can you launch firefox for me

# VS Code variations:
> open vs code
> launch vscode
> start visual studio code
> open code

# Category-based:
> open browser       → Suggests Firefox, Chrome, etc.
> launch editor      → Suggests Gedit, VS Code, etc.
> start media player → Suggests VLC, MPV, etc.
```

### GUI Features

- **Search Bar** - Type to filter apps instantly
- **Favorites** - Click ⭐ to pin apps for quick access
- **Categories** - Apps are organized by type
- **History** - Frequently used apps appear first
- **Settings** - Configure AI provider, notifications, etc.

## 🏗️ Architecture

```
aipp_opener/
├── cli.py              # Command-line interface
├── gui.py              # GUI frontend (tkinter)
├── tray.py             # System tray integration
├── keyboard.py         # Keyboard shortcuts (X11/Wayland)
├── wayland_shortcuts.py # Wayland XDG Desktop Portal support
├── config.py           # Configuration (pydantic)
├── executor.py         # Application execution
├── voice.py            # Voice input
├── history.py          # Usage history
├── categories.py       # App categorization
├── icons.py            # Icon detection
├── cache.py            # Caching layer with TTL
├── aliases.py          # Custom command aliases
├── groups.py           # App groups/workspaces
├── web_search.py       # Web search with custom engines
├── plugins.py          # Plugin system with security
├── detectors/          # App detection modules
│   ├── base.py         # Abstract detector
│   ├── nixos.py        # NixOS detection (cached)
│   ├── debian.py       # Debian detection (cached)
│   ├── fedora.py       # Fedora/RHEL detection (cached)
│   └── arch.py         # Arch Linux detection (cached)
├── ai/                 # AI/NLP processing
│   ├── base.py         # AI provider interface
│   ├── ollama.py       # Ollama (local)
│   ├── gemini.py       # Google Gemini
│   ├── openai.py       # OpenAI
│   ├── openrouter.py   # OpenRouter
│   └── nlp.py          # NLP utilities
└── plugins/            # User plugins directory
    ├── custom_commands.py
    ├── docker_detector.py
    ├── notification_modifier.py
    ├── recent_files.py
    └── browser_tabs.py
```

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=aipp_opener

# Test specific module
python -m pytest tests/test_new_modules.py

# Current test status: 43 tests passing
```

## 📊 Test Coverage

| Module | Coverage |
|--------|----------|
| web_search.py | 93% |
| plugins.py | 62% |
| aliases.py | 61% |
| groups.py | 57% |
| cache.py | 70% |
| **Overall** | 13% |

Target: 80% coverage for Phase 4.

## 🔧 Troubleshooting

### GUI Not Opening

Make sure tkinter is installed:
```bash
# NixOS
nix-env -iA nixpkgs.python311Packages.tkinter

# Debian/Ubuntu
sudo apt install python3-tk
```

### System Tray Not Working

Install pystray and pillow:
```bash
pip install pystray pillow
```

### Keyboard Shortcuts Not Working

**For X11:**
Install pynput:
```bash
pip install pynput python-xlib
```

**For Wayland:**
The app now supports Wayland global shortcuts via XDG Desktop Portal!

Requirements:
- `xdg-desktop-portal` (usually pre-installed on Wayland sessions)
- `python-dbus` and `pygobject` for D-Bus communication

```bash
# Debian/Ubuntu
sudo apt install python3-dbus python3-gi

# Fedora
sudo dnf install python3-dbus python3-gobject

# Arch
sudo pacman -S python-dbus python-gobject
```

The app automatically detects your session type (X11 or Wayland) and uses the appropriate backend.

**Note:** Wayland GlobalShortcuts portal support depends on your compositor:
- **GNOME 48+**: Full support with configuration UI
- **KDE Plasma**: Full support with GUI
- **Hyprland**: Limited support (requires manual config)
- **wlroots**: Not yet supported

### Voice Input Not Working

```bash
# Install PortAudio
sudo apt install portaudio19-dev

# Install SpeechRecognition
pip install SpeechRecognition PyAudio
```

### Ollama Connection Error

Make sure Ollama is running:
```bash
ollama serve
```

Check model is available:
```bash
ollama list
ollama pull llama3.2
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines, development setup, code style, and testing instructions
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md)** - Plugin development guide and API reference
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details for v0.3.0
- **[CONTAINER_TESTING.md](CONTAINER_TESTING.md)** - Guide for testing in Docker/Podman containers
- **[PROJECT.md](PROJECT.md)** - Project overview and quick reference

## 🗺️ Roadmap

### Phase 4 [v0.6.0] - Current
- ✅ Custom search engines with user-defined options
- ✅ Plugin security model with sandboxing
- ✅ Sample plugins (recent files, browser tabs)
- 🔄 Test coverage expansion (target: 80%)
- ⏳ Performance profiling tools

### Phase 5 [v0.7.0] - Future
- Async/await patterns for I/O operations
- Systemd user service for background operations
- Flatpak/Snap packaging
- Enhanced AI features (context-aware suggestions)

## 📈 Recent Changes (v0.6.0)

- **Plugin System** - Extensible plugin architecture with security model
- **Custom Search Engines** - Add your own search engines or use 7 built-in options
- **Recent Files Plugin** - Quick access to GTK recent documents
- **Browser Tabs Plugin** - Detect and switch to open browser tabs
- **Wayland Support** - Global keyboard shortcuts via XDG Desktop Portal
- **Fedora/Arch Support** - App detection for additional Linux distributions
- **Caching Layer** - 10-minute TTL cache for faster app detection
- **Lazy Loading GUI** - Non-blocking startup (~100ms)

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local AI inference
- [Google Gemini](https://ai.google.dev/) for AI capabilities
- [OpenAI](https://openai.com/) for GPT models
- [OpenRouter](https://openrouter.ai/) for multi-model access
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy string matching
- [pynput](https://github.com/moses-palmer/pynput) for keyboard/mouse control
- [pystray](https://github.com/moses-palmer/pystray) for system tray icons
