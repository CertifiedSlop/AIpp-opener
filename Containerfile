# Containerfile for AIpp Opener with Ollama
# Build: podman build -t aipp-opener .
# Run: podman run --rm -it -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix aipp-opener

FROM docker.io/library/python:3.11-slim-bookworm

LABEL name="aipp-opener"
LABEL description="AI-powered application launcher with Ollama"
LABEL version="0.2.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # X11 dependencies for GUI
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    # Audio for voice input
    libasound2 \
    libportaudio2 \
    # Notifications
    libnotify4 \
    # Utilities
    curl \
    ca-certificates \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install core Python dependencies (skip keyboard shortcuts which need kernel headers)
RUN pip install --no-cache-dir \
    requests>=2.31.0 \
    fuzzywuzzy>=0.18.0 \
    python-Levenshtein>=0.23.0 \
    pydantic>=2.5.0 \
    pyyaml>=6.0.1 \
    pillow>=10.0.0 \
    pystray>=0.19.5 \
    notify-py>=0.3.42 \
    pytest>=7.4.0

# Copy application code
COPY aipp_opener/ ./aipp_opener/
COPY pyproject.toml .
COPY tests/ ./tests/

# Install the package
RUN pip install -e .

# Create config directory and default config
RUN mkdir -p /root/.config/aipp_opener && \
    printf '%s\n' '{' \
        '  "ai": {' \
        '    "provider": "ollama",' \
        '    "model": "tinyllama",' \
        '    "base_url": "http://ollama:11434"' \
        '  },' \
        '  "voice_enabled": false,' \
        '  "notifications_enabled": false,' \
        '  "history_enabled": true,' \
        '  "max_suggestions": 5,' \
        '  "default_shell": "bash"' \
        '}' > /root/.config/aipp_opener/config.json

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from aipp_opener import __version__; print(__version__)" || exit 1

# Default command
CMD ["python", "-m", "aipp_opener", "--interactive"]
