# Container Testing Guide

This guide explains how to test AIpp Opener inside a Podman/Docker container.

## Quick Start

### Build the Container

```bash
# Using Podman
podman build -t aipp-opener:latest .

# Using Docker
docker build -t aipp-opener:latest .
```

### Run Tests

```bash
# Check version
podman run --rm aipp-opener:latest python -c "from aipp_opener import __version__; print(__version__)"

# Run unit tests
podman run --rm aipp-opener:latest python -m pytest tests/ -v --override-ini="addopts="

# Test app detection
podman run --rm aipp-opener:latest python -m aipp_opener --list-apps

# Test categorization
podman run --rm aipp-opener:latest python -c "
from aipp_opener.categories import AppCategorizer
c = AppCategorizer()
for app in ['firefox', 'code', 'vlc', 'gimp']:
    print(f'{app}: {c.categorize(app).value}')
"
```

### Run Interactive Mode

```bash
# Note: This won't actually launch apps in a container
# but you can test the NLP and suggestion features
podman run --rm -it aipp-opener:latest python -m aipp_opener --interactive
```

### Run with Docker Compose (includes Ollama)

```bash
# Start Ollama and AIpp Opener
docker compose up -d

# Check logs
docker compose logs -f aipp-opener

# Stop
docker compose down
```

## Container Features

### Included Dependencies

- **Core**: requests, fuzzywuzzy, python-Levenshtein, pydantic, pyyaml
- **GUI**: pillow, pystray (tkinter available in base Python)
- **Notifications**: notify-py
- **Testing**: pytest

### Not Included (Optional)

- **Keyboard shortcuts**: Requires kernel headers (pynput, evdev)
- **Voice input**: Requires PortAudio and audio device access
- **AI providers**: Ollama runs in separate container (see docker-compose.yml)

## Testing Specific Features

### NLP Processing

```bash
podman run --rm aipp-opener:latest python -c "
from aipp_opener.ai.nlp import NLPProcessor
nlp = NLPProcessor()

# Test intent extraction
commands = [
    'open firefox',
    'launch vs code', 
    'start the browser please',
    'run spotify'
]

print('Intent Extraction:')
for cmd in commands:
    print(f'  {cmd!r} -> {nlp.extract_app_intent(cmd)!r}')

# Test fuzzy matching
print()
print('Fuzzy Matching:')
candidates = ['firefox', 'chromium', 'brave']
for query in ['firefux', 'chrome', 'vivaldi']:
    matches = nlp.find_best_match(query, candidates)
    print(f'  {query!r} -> {matches}')
"
```

### App Categories

```bash
podman run --rm aipp-opener:latest python -c "
from aipp_opener.categories import AppCategorizer, AppCategory

categorizer = AppCategorizer()

# Test all categories
apps = {
    'Browser': ['firefox', 'chrome', 'chromium', 'brave'],
    'Editor': ['gedit', 'kate', 'vim', 'emacs'],
    'IDE': ['code', 'pycharm', 'intellij'],
    'Media': ['vlc', 'mpv', 'rhythmbox'],
    'Graphics': ['gimp', 'inkscape', 'krita', 'blender'],
    'Communication': ['discord', 'slack', 'zoom', 'telegram'],
    'Game': ['steam', 'lutris', 'heroic'],
    'System': ['nautilus', 'dolphin', 'settings'],
}

for category, apps_list in apps.items():
    print(f'{category}:')
    for app in apps_list:
        cat = categorizer.categorize(app)
        match = '✓' if cat.value == category.lower() else '✗'
        print(f'  {match} {app} -> {cat.value}')
    print()
"
```

### Configuration

```bash
# View default config
podman run --rm aipp-opener:latest cat /root/.config/aipp_opener/config.json

# Test config loading
podman run --rm aipp-opener:latest python -c "
from aipp_opener.config import ConfigManager
config = ConfigManager()
print('Provider:', config.get().ai.provider)
print('Model:', config.get().ai.model)
print('History:', config.get().history_enabled)
"
```

### History Management

```bash
podman run --rm aipp-opener:latest python -c "
from aipp_opener.history import HistoryManager
import tempfile
from pathlib import Path

# Create temp history file
temp_file = Path(tempfile.mktemp(suffix='.json'))
history = HistoryManager(history_file=temp_file)

# Record some launches
history.record('open firefox', 'firefox', '/usr/bin/firefox')
history.record('open firefox', 'firefox', '/usr/bin/firefox')
history.record('open code', 'code', '/usr/bin/code')

# Get stats
stats = history.get_stats()
print('Stats:', stats)

# Get frequent apps
frequent = history.get_frequent_apps(5)
print('Frequent:', frequent)

# Cleanup
temp_file.unlink()
"
```

## Troubleshooting

### GUI in Container

To run the GUI, you need X11 forwarding:

```bash
# Allow local connections to X server
xhost +local:

# Run with X11 socket mounted
podman run --rm -it \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    aipp-opener:latest python -m aipp_opener --gui
```

### Voice Input in Container

Voice input requires audio device access:

```bash
# Run with PulseAudio socket
podman run --rm -it \
    -e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
    -v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
    --group-add $(getent group audio | cut -d: -f3) \
    aipp-opener:latest python -m aipp_opener --voice
```

Note: Voice dependencies (PyAudio) are not installed in the base container.

### Keyboard Shortcuts in Container

Keyboard shortcuts require additional kernel headers and are not included in the container by default. To add them:

```dockerfile
# Add to Containerfile
RUN apt-get update && apt-get install -y \
    linux-headers-amd64 \
    && pip install pynput python-xlib
```

## Performance Notes

- Container startup time: ~2 seconds
- App detection in container: ~1-2 seconds (556 apps)
- NLP processing: <100ms per query
- Unit tests: <1 second (37 tests)

## Next Steps

1. Test with Ollama integration (see docker-compose.yml)
2. Test GUI mode with X11 forwarding
3. Integrate into your CI/CD pipeline
4. Create custom container with additional dependencies
