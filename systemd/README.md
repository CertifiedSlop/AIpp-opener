# AIpp Opener - Systemd User Service Setup

This directory contains systemd user service files for AIpp Opener.

## Installation

### 1. Copy service files to user systemd directory

```bash
# Create systemd user directory if it doesn't exist
mkdir -p ~/.config/systemd/user

# Copy service files
cp systemd/*.service ~/.config/systemd/user/
cp systemd/*.timer ~/.config/systemd/user/
```

### 2. Enable and start the main service

```bash
# Reload systemd to recognize new services
systemctl --user daemon-reload

# Enable the service to start on boot
systemctl --user enable aipp-opener.service

# Start the service immediately
systemctl --user start aipp-opener.service

# Check status
systemctl --user status aipp-opener.service
```

### 3. Enable the cleanup timer

```bash
# Enable the daily cleanup timer
systemctl --user enable aipp-opener-cleanup.timer

# Start the timer immediately
systemctl --user start aipp-opener-cleanup.timer

# Check timer status
systemctl --user list-timers | grep aipp-opener
```

## Service Descriptions

### aipp-opener.service
- Runs AIpp Opener in the system tray
- Automatically restarts on failure
- Includes security hardening (read-only system, restricted network, etc.)
- Writes to allowed directories only

### aipp-opener-cleanup.service
- Cleans up expired cache entries
- Runs daily via the timer
- Maintains optimal performance

### aipp-opener-cleanup.timer
- Triggers the cleanup service daily
- Starts 5 minutes after boot
- Persists across reboots

## Management Commands

```bash
# View service status
systemctl --user status aipp-opener.service

# View logs
journalctl --user -u aipp-opener.service -f

# Stop the service
systemctl --user stop aipp-opener.service

# Restart the service
systemctl --user restart aipp-opener.service

# Disable the service
systemctl --user disable aipp-opener.service

# View timer status
systemctl --user list-timers | grep aipp-opener
```

## Troubleshooting

### Service won't start

1. Check if Python and aipp_opener are installed:
   ```bash
   python3 -m aipp_opener --version
   ```

2. Check logs:
   ```bash
   journalctl --user -u aipp-opener.service -n 50
   ```

3. Verify config directory permissions:
   ```bash
   ls -la ~/.config/aipp_opener/
   ```

### Tray icon not showing

- Ensure you have a system tray applet running (e.g., `gnome-shell-extension-appindicator`)
- Check if pystray is installed: `pip show pystray`

### Cleanup timer not running

1. Check timer status:
   ```bash
   systemctl --user list-timers | grep aipp-opener
   ```

2. Manually trigger cleanup:
   ```bash
   systemctl --user start aipp-opener-cleanup.service
   ```

## Uninstall

```bash
# Stop and disable services
systemctl --user stop aipp-opener.service
systemctl --user disable aipp-opener.service
systemctl --user stop aipp-opener-cleanup.timer
systemctl --user disable aipp-opener-cleanup.timer

# Remove service files
rm ~/.config/systemd/user/aipp-opener*.service
rm ~/.config/systemd/user/aipp-opener*.timer

# Reload systemd
systemctl --user daemon-reload
```
