# AIpp Opener Plugin Development Guide

## Overview

The AIpp Opener plugin system allows you to extend the functionality of AIpp Opener with custom features. Plugins can add new app detectors, custom commands, or modify execution results.

## Installation

### User Plugins Directory
Place your plugin files in:
```
~/.local/share/aipp_opener/plugins/
```

### System-wide Plugins Directory
For system-wide installation:
```
/usr/local/share/aipp_opener/plugins/
```

## Plugin Types

### 1. AppDetectorPlugin

Detects applications on your system and makes them available to AIpp Opener.

```python
from aipp_opener.plugins import AppDetectorPlugin
from aipp_opener.detectors.base import AppInfo

class MyDetectorPlugin(AppDetectorPlugin):
    @property
    def name(self) -> str:
        return "my_detector"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Detects my custom applications"
    
    def is_available(self) -> bool:
        """Check if this detector is available on the current system."""
        # Return True if your detection method is available
        return True
    
    def detect(self) -> list[AppInfo]:
        """Detect applications and return a list of AppInfo objects."""
        apps = []
        
        # Example: Detect a custom application
        apps.append(AppInfo(
            name="myapp",
            executable="/usr/bin/myapp",
            display_name="My Application",
            description="A custom application",
            categories=["Utilities"],
        ))
        
        return apps
```

### 2. CommandPlugin

Adds custom commands that can be invoked from the CLI or GUI.

```python
from aipp_opener.plugins import CommandPlugin
from typing import Callable

class MyCommandsPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "my_commands"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Adds custom commands"
    
    def get_commands(self) -> dict[str, Callable]:
        """Return a dictionary of command names to callables."""
        return {
            "hello": self.say_hello,
            "info": self.show_info,
        }
    
    def say_hello(self) -> None:
        """Say hello."""
        print("Hello from AIpp Opener!")
    
    def show_info(self) -> None:
        """Show system information."""
        import platform
        print(f"System: {platform.system()}")
        print(f"Release: {platform.release()}")
        print(f"Machine: {platform.machine()}")
```

### 3. ResultModifierPlugin

Modifies execution results (e.g., add notifications, logging, analytics).

```python
from aipp_opener.plugins import ResultModifierPlugin
from aipp_opener.executor import ExecutionResult

class MyModifierPlugin(ResultModifierPlugin):
    @property
    def name(self) -> str:
        return "my_modifier"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Modifies execution results"
    
    def modify_result(self, result: ExecutionResult) -> ExecutionResult:
        """Modify an execution result."""
        # Add custom logging
        self._log_execution(result)
        
        # Show notification
        self._notify(result)
        
        return result
    
    def _log_execution(self, result: ExecutionResult) -> None:
        """Log the execution."""
        # Your logging logic here
        pass
    
    def _notify(self, result: ExecutionResult) -> None:
        """Show notification."""
        # Your notification logic here
        pass
```

## Plugin Lifecycle

### on_load()

Called when the plugin is loaded. Use this for initialization.

```python
def on_load(self) -> None:
    """Initialize plugin resources."""
    self._config = self._load_config()
    logger.info("Plugin loaded: %s", self.name)
```

### on_unload()

Called when the plugin is unloaded. Use this for cleanup.

```python
def on_unload(self) -> None:
    """Clean up plugin resources."""
    self._save_config()
    logger.info("Plugin unloaded: %s", self.name)
```

## Plugin Management

### CLI Commands

```bash
# List all plugins
python -m aipp_opener --plugins

# Get plugin information
python -m aipp_opener --plugin-info my_plugin

# Enable a plugin
python -m aipp_opener --enable-plugin my_plugin

# Disable a plugin
python -m aipp_opener --disable-plugin my_plugin
```

### Programmatic Management

```python
from aipp_opener.plugins import PluginManager

manager = PluginManager()

# Load all plugins from default directory
manager.load_all_plugins()

# Get plugin by name
plugin = manager.get_plugin("my_plugin")

# Get all enabled plugins
enabled = manager.get_enabled_plugins()

# Get specific plugin types
detectors = manager.get_detector_plugins()
commands = manager.get_command_plugins()
modifiers = manager.get_result_modifier_plugins()

# Enable/disable plugins
manager.enable_plugin("my_plugin")
manager.disable_plugin("my_plugin")

# Get plugin statistics
stats = manager.get_stats()
print(f"Total plugins: {stats['total_plugins']}")
print(f"Enabled plugins: {stats['enabled_plugins']}")
```

## Plugin Configuration

Plugins can store configuration in `~/.local/share/aipp_opener/plugins.json`:

```json
{
  "plugins": {
    "my_plugin": {
      "enabled": true,
      "config": {
        "option1": "value1",
        "option2": "value2"
      }
    }
  }
}
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
def detect(self) -> list[AppInfo]:
    try:
        # Your detection logic
        return apps
    except Exception as e:
        logger.error("Error in detector: %s", e)
        return []
```

### 2. Logging

Use the built-in logger:

```python
from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### 3. Performance

- Keep detection fast and efficient
- Use caching when appropriate
- Avoid blocking operations in callbacks

### 4. Dependencies

- Minimize external dependencies
- Handle missing dependencies gracefully
- Document required dependencies

### 5. Security

- Don't execute arbitrary code
- Validate all inputs
- Don't store sensitive information in plain text

## Example Plugins

See the `plugins/` directory in the AIpp Opener repository for complete examples:

- `docker_detector.py` - Detects Docker containers
- `custom_commands.py` - Adds system commands
- `notification_modifier.py` - Shows desktop notifications

## Testing Plugins

Create a test file for your plugin:

```python
import unittest
from my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
    
    def test_name(self):
        self.assertEqual(self.plugin.name, "my_plugin")
    
    def test_version(self):
        self.assertEqual(self.plugin.version, "1.0.0")
    
    def test_detection(self):
        apps = self.plugin.detect()
        self.assertIsInstance(apps, list)

if __name__ == "__main__":
    unittest.main()
```

## Publishing Plugins

To share your plugin with the community:

1. Create a GitHub repository
2. Add a README with installation instructions
3. Include a LICENSE file
4. Submit a PR to the AIpp Opener plugin list

## Troubleshooting

### Plugin not loading

Check the log file:
```bash
cat ~/.local/state/aipp_opener/aipp_opener.log
```

### Plugin causes errors

1. Disable the plugin:
   ```bash
   python -m aipp_opener --disable-plugin my_plugin
   ```

2. Check for syntax errors:
   ```bash
   python -m py_compile ~/.local/share/aipp_opener/plugins/my_plugin.py
   ```

3. Review the plugin code for issues

## API Reference

### AppInfo

```python
class AppInfo:
    name: str                    # Application name
    executable: str              # Path to executable
    display_name: str            # Display name
    description: str             # Description
    categories: list[str]        # Categories
    icon: str                    # Icon name/path
```

### ExecutionResult

```python
class ExecutionResult:
    success: bool                # Whether execution succeeded
    app_name: str                # Application name
    executable: str              # Executable path
    output: str                  # Command output
    error: str                   # Error message
    return_code: int             # Exit code
```

## Support

For questions or issues:
- GitHub Issues: https://github.com/CertifiedSlop/AIpp-opener/issues
- Documentation: https://github.com/CertifiedSlop/AIpp-opener/wiki/Plugins

## License

Plugins should be compatible with AIpp Opener's MIT license.
