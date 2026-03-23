# Flatpak Build Instructions for AIpp Opener

## Prerequisites

Install Flatpak and the Freedesktop runtime:

```bash
# On Fedora
sudo dnf install flatpak flatpak-builder

# On Debian/Ubuntu
sudo apt install flatpak flatpak-builder

# On Arch Linux
sudo pacman -S flatpak flatpak-builder
```

Add the Flathub repository:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

Install the required runtime and SDK:

```bash
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
```

## Build the Flatpak

### Option 1: Build locally

```bash
# Create a build directory
mkdir -p flatpak-build

# Build the application
flatpak-builder --repo=flatpak-repo --force-clean flatpak-build flatpak/io.github.CertifiedSlop.AIppOpener.json

# Test the application
flatpak --install flatpak-repo io.github.CertifiedSlop.AIppOpener
flatpak run io.github.CertifiedSlop.AIppOpener --gui
```

### Option 2: Build and install directly

```bash
flatpak-builder --install --user flatpak-build flatpak/io.github.CertifiedSlop.AIppOpener.json
```

## Create a Flatpak Bundle

To distribute a single-file bundle:

```bash
# Export the application as a .flatpak file
flatpak build-bundle flatpak-repo aipp-opener.flatpak io.github.CertifiedSlop.AIppOpener

# Install from the bundle
flatpak install --user aipp-opener.flatpak

# Run the application
flatpak run io.github.CertifiedSlop.AIppOpener --gui
```

## Debugging

### Run with verbose output

```bash
flatpak run --verbose io.github.CertifiedSlop.AIppOpener
```

### Access the build directory

```bash
flatpak-builder --run flatpak-build flatpak/io.github.CertifiedSlop.AIppOpener.json bash
```

### Check installed files

```bash
ls -la ~/.var/app/io.github.CertifiedSlop.AIppOpener/
```

## Publish to Flathub

1. Fork the [flathub/flathub](https://github.com/flathub/flathub) repository
2. Create a pull request with your app manifest
3. Follow the [Flathub submission guidelines](https://docs.flathub.org/docs/for-app-authors/submission/)

Required files for Flathub:
- `io.github.CertifiedSlop.AIppOpener.json` (app manifest)
- `io.github.CertifiedSlop.AIppOpener.metainfo.xml` (AppStream metadata)
- `io.github.CertifiedSlop.AIppOpener.desktop` (desktop file)
- `io.github.CertifiedSlop.AIppOpener.svg` (application icon)

## Known Limitations

1. **Keyboard shortcuts**: Global keyboard shortcuts require additional permissions and may not work in sandboxed environment
2. **Ollama integration**: Requires network access to localhost:11434 (add `--socket=network` if needed)
3. **Voice input**: Requires pulseaudio/socket permissions
4. **System tray**: May not work in all desktop environments when sandboxed

## Troubleshooting

### Application won't start

Check permissions:
```bash
flatpak info --show-permissions io.github.CertifiedSlop.AIppOpener
```

### Missing dependencies

Add required modules to the JSON manifest or use:
```bash
flatpak install flathub <missing-dependency>
```

### Permission issues

Override permissions:
```bash
flatpak override --user --filesystem=home io.github.CertifiedSlop.AIppOpener
```

## Uninstall

```bash
flatpak uninstall io.github.CertifiedSlop.AIppOpener
flatpak-builder --cleanup
```
