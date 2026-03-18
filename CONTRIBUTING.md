# Contributing to AIpp Opener

Thank you for your interest in contributing to AIpp Opener! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/your-username/aipp-opener.git
   cd aipp-opener
   ```
3. **Set up the development environment** (see below)
4. **Create a branch** for your feature
   ```bash
   git checkout -b feature/amazing-feature
   ```

## Development Setup

### NixOS

```bash
nix-shell shell.nix
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Debian/Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Code Style

We use the following tools to maintain code quality:

- **Black** - Code formatting
- **Ruff** - Linting (replaces flake8, isort, and more)
- **Mypy** - Type checking

### Running Linters

```bash
# Check code style
ruff check aipp_opener/ tests/

# Format code
black aipp_opener/ tests/

# Type checking
mypy aipp_opener/ --ignore-missing-imports
```

### Pre-commit Hooks

We recommend using pre-commit hooks to automatically check your code before committing:

```bash
pre-commit install
```

Pre-commit will automatically run checks on staged files before each commit.

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=aipp_opener --cov-report=html

# Run specific test file
pytest tests/test_aipp_opener.py

# Run specific test
pytest tests/test_aipp_opener.py::TestNLPProcessor::test_extract_app_intent_simple
```

### Writing Tests

- Write tests for new features
- Keep tests focused and independent
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern

Example:

```python
def test_extract_app_intent_simple():
    """Test extracting app name from simple command."""
    nlp = NLPProcessor()
    result = nlp.extract_app_intent("open firefox")
    assert result == "firefox"
```

## Pull Requests

### Before Submitting

1. **Run tests** - Ensure all tests pass
   ```bash
   pytest tests/
   ```

2. **Run linters** - Fix any issues
   ```bash
   ruff check aipp_opener/ tests/
   black --check aipp_opener/ tests/
   ```

3. **Update documentation** - Add docstrings, update README if needed

4. **Add tests** - Include tests for new features

### Submitting

1. **Commit messages** - Follow conventional commits:
   - `feat: Add new feature`
   - `fix: Fix bug in executor`
   - `docs: Update README`
   - `test: Add tests for NLP processor`
   - `refactor: Improve code structure`

2. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

3. **Open a Pull Request** on GitHub
   - Describe your changes
   - Reference any related issues
   - Include screenshots if applicable

### Review Process

- Maintainers will review your PR
- Address any feedback
- Once approved, your PR will be merged

## Reporting Issues

### Bug Reports

When reporting a bug, include:

1. **Description** - Clear description of the issue
2. **Steps to Reproduce** - How to reproduce the bug
3. **Expected Behavior** - What should happen
4. **Actual Behavior** - What actually happens
5. **Environment**:
   - OS (NixOS, Debian, Ubuntu, etc.)
   - Python version
   - AIpp Opener version
6. **Logs** - Run with `--log-level DEBUG` and include relevant logs

Example:

```markdown
**Description**
App fails to launch when using voice command.

**Steps to Reproduce**
1. Run `aipp-opener --voice`
2. Say "open firefox"
3. Application crashes

**Expected Behavior**
Firefox should launch

**Actual Behavior**
Error: "Executable not found"

**Environment**
- OS: NixOS 23.11
- Python: 3.11.14
- AIpp Opener: 0.3.0-dev

**Logs**
[Debug logs here]
```

### Feature Requests

For feature requests, include:

1. **Problem** - What problem does this solve?
2. **Solution** - How should it work?
3. **Alternatives** - What alternatives have you considered?
4. **Use Case** - Who will benefit from this?

## Architecture Overview

```
aipp_opener/
├── cli.py              # Command-line interface
├── gui.py              # GUI frontend
├── tray.py             # System tray integration
├── keyboard.py         # Keyboard shortcuts
├── config.py           # Configuration management
├── executor.py         # Application execution
├── voice.py            # Voice input
├── history.py          # Usage history
├── categories.py       # App categorization
├── icons.py            # Icon detection
├── logger_config.py    # Logging configuration
├── setup_wizard.py     # First-time setup
├── detectors/          # Platform-specific app detection
│   ├── base.py
│   ├── nixos.py
│   └── debian.py
└── ai/                 # AI providers
    ├── base.py
    ├── ollama.py
    ├── gemini.py
    ├── openai.py
    └── openrouter.py
```

## Questions?

- Check the [README.md](README.md) for general documentation
- Look at existing [issues](https://github.com/aipp-opener/aipp-opener/issues)
- Join discussions in [Discussions](https://github.com/aipp-opener/aipp-opener/discussions)

Thank you for contributing! 🎉
