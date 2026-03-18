# AIpp Opener - Application and System Utilities

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NixOS](https://img.shields.io/badge/NixOS-supported-blue.svg)](https://nixos.org/)
[![Debian](https://img.shields.io/badge/Debian-supported-red.svg)](https://www.debian.org/)

AI-powered application launcher for Linux. Open applications using natural language commands with support for multiple AI providers.

## Quick Start

```bash
# NixOS users
nix-shell shell.nix
pip install -r requirements.txt

# Run
python -m aipp_opener "open firefox"
```

## Features

- 🎯 Natural language commands ("open Firefox", "launch VS Code")
- 🤖 Multiple AI providers (Ollama, Gemini, OpenAI, OpenRouter)
- 🔍 Smart app detection for NixOS and Debian
- 🎤 Optional voice input
- 📝 Usage history and predictions
- 🔔 System notifications

## Documentation

See [README.md](README.md) for full documentation including:
- Installation instructions
- Usage examples
- Configuration options
- Troubleshooting guide

## License

MIT License
