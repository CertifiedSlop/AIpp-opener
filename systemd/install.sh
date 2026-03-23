#!/usr/bin/env bash
# Install systemd user services for AIpp Opener

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "Installing AIpp Opener systemd user services..."

# Create systemd user directory if it doesn't exist
mkdir -p "$SYSTEMD_USER_DIR"

# Copy service files
echo "Copying service files to $SYSTEMD_USER_DIR..."
cp "$SCRIPT_DIR"/*.service "$SYSTEMD_USER_DIR/"
cp "$SCRIPTD_DIR"/*.timer "$SYSTEMD_USER_DIR/" 2>/dev/null || true

# Reload systemd
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

# Enable services
echo "Enabling services..."
systemctl --user enable aipp-opener.service 2>/dev/null || echo "  (Note: aipp-opener.service enable failed)"
systemctl --user enable aipp-opener-cleanup.timer 2>/dev/null || echo "  (Note: cleanup timer enable failed)"

echo ""
echo "Installation complete!"
echo ""
echo "To start the main service:"
echo "  systemctl --user start aipp-opener.service"
echo ""
echo "To start the cleanup timer:"
echo "  systemctl --user start aipp-opener-cleanup.timer"
echo ""
echo "To check status:"
echo "  systemctl --user status aipp-opener.service"
echo "  systemctl --user list-timers | grep aipp-opener"
