"""Wayland global keyboard shortcuts support via XDG Desktop Portal."""

import os
import secrets
import re
from typing import Optional, Callable, Any
from dataclasses import dataclass

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib

    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False


@dataclass
class ShortcutBinding:
    """Represents a bound keyboard shortcut."""

    shortcut_id: str
    description: str
    trigger: Optional[str] = None
    callback: Optional[Callable] = None


class WaylandShortcutSession:
    """Global keyboard shortcut handler for Wayland using XDG Desktop Portal."""

    # D-Bus interface constants
    PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
    PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
    PORTAL_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
    REQUEST_INTERFACE = "org.freedesktop.portal.Request"
    SESSION_INTERFACE = "org.freedesktop.portal.Session"

    def __init__(self):
        """Initialize the Wayland shortcut session."""
        self._bus: Optional[dbus.Bus] = None
        self._portal: Optional[dbus.ProxyObject] = None
        self._session_handle: Optional[str] = None
        self._shortcuts: dict[str, ShortcutBinding] = {}
        self._main_loop: Optional[GLib.MainLoop] = None
        self._running = False
        self._request_counter = 0

    def is_available(self) -> bool:
        """Check if Wayland global shortcuts are available."""
        if not DBUS_AVAILABLE:
            logger.debug("D-Bus libraries not available")
            return False

        # Check if running on Wayland
        if not self._is_wayland_session():
            logger.debug("Not running on Wayland")
            return False

        try:
            # Try to connect to the portal
            DBusGMainLoop(set_as_default=True)
            self._bus = dbus.SessionBus()
            self._portal = self._bus.get_object(
                self.PORTAL_BUS_NAME, self.PORTAL_OBJECT_PATH
            )

            # Check if the portal supports GlobalShortcuts
            introspect = dbus.Interface(
                self._portal, "org.freedesktop.DBus.Introspectable"
            )
            xml = introspect.Introspect()

            if self.PORTAL_INTERFACE not in xml:
                logger.debug("GlobalShortcuts interface not available in portal")
                return False

            logger.info("Wayland GlobalShortcuts portal is available")
            return True

        except dbus.DBusException as e:
            logger.debug(f"D-Bus error: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error checking Wayland shortcuts availability: {e}")
            return False

    def _is_wayland_session(self) -> bool:
        """Detect if running under a Wayland session."""
        # Check environment variables
        wayland_indicators = [
            os.environ.get("WAYLAND_DISPLAY"),
            os.environ.get("XDG_SESSION_TYPE") == "wayland",
            os.environ.get("DESKTOP_SESSION") == "wayland",
        ]

        if any(wayland_indicators):
            return True

        # Check if X11 is NOT running (heuristic)
        if not os.environ.get("DISPLAY"):
            # No DISPLAY and no explicit X11 indicator might mean Wayland
            return True

        return False

    def _generate_handle_token(self, prefix: str = "request") -> str:
        """Generate a unique handle token."""
        self._request_counter += 1
        return f"{prefix}_{self._sender_name()}_{self._request_counter}_{secrets.token_hex(8)}"

    def _sender_name(self) -> str:
        """Get the sender name from the D-Bus connection."""
        if self._bus:
            unique_name = self._bus.get_unique_name()
            return re.sub(r"\.", "_", unique_name).lstrip(":")
        return "unknown"

    def _request_handle(self, token: str) -> str:
        """Build the request object path."""
        return f"{self.PORTAL_OBJECT_PATH}/request/{self._sender_name()}/{token}"

    def _session_handle(self, token: str) -> str:
        """Build the session object path."""
        return f"{self.PORTAL_OBJECT_PATH}/session/{self._sender_name()}/{token}"

    def _on_response(
        self, response: int, results: dict[str, Any], callback: Callable
    ) -> None:
        """Handle D-Bus response signal."""
        if response == 0:  # Success
            callback(results)
        else:
            logger.warning(f"Portal request failed with response code: {response}")

    def create_session(self) -> bool:
        """Create a global shortcuts session."""
        if not self._portal:
            logger.error("Portal not initialized")
            return False

        try:
            session_token = self._generate_handle_token("session")
            session_handle = self._session_handle(session_token)

            # Create the session
            portal_interface = dbus.Interface(self._portal, self.PORTAL_INTERFACE)

            request_token = self._generate_handle_token("create")
            request_handle = self._request_handle(request_token)

            options = {
                "handle_token": request_token,
                "session_handle_token": session_token,
            }

            # Set up response listener
            self._bus.add_signal_receiver(
                self._on_create_session_response,
                "Response",
                self.REQUEST_INTERFACE,
                self.PORTAL_BUS_NAME,
                request_handle,
            )

            # Call CreateSession
            portal_interface.CreateSession(options, dbus_interface=self.PORTAL_INTERFACE)

            # Run the main loop briefly to get the response
            self._wait_for_response(timeout=5000)

            return self._session_handle is not None

        except dbus.DBusException as e:
            logger.error(f"D-Bus error creating session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def _on_create_session_response(self, response: int, results: dict[str, Any]) -> None:
        """Handle CreateSession response."""
        if response == 0 and "session_handle" in results:
            self._session_handle = results["session_handle"]
            logger.info(f"Created session: {self._session_handle}")

            # Set up signal receivers for this session
            self._setup_signal_receivers()
        else:
            logger.warning(f"Failed to create session: response={response}")

    def _setup_signal_receivers(self) -> None:
        """Set up D-Bus signal receivers for shortcut events."""
        if not self._session_handle or not self._bus:
            return

        # Listen for Activated signals
        self._bus.add_signal_receiver(
            self._on_shortcut_activated,
            "Activated",
            self.PORTAL_INTERFACE,
            self.PORTAL_BUS_NAME,
            path_keyword="session_handle",
        )

        # Listen for Deactivated signals
        self._bus.add_signal_receiver(
            self._on_shortcut_deactivated,
            "Deactivated",
            self.PORTAL_INTERFACE,
            self.PORTAL_BUS_NAME,
            path_keyword="session_handle",
        )

        # Listen for ShortcutsChanged signals
        self._bus.add_signal_receiver(
            self._on_shortcuts_changed,
            "ShortcutsChanged",
            self.PORTAL_INTERFACE,
            self.PORTAL_BUS_NAME,
            path_keyword="session_handle",
        )

    def _on_shortcut_activated(
        self,
        session_handle: str,
        shortcut_id: str,
        timestamp: int,
        options: dict[str, Any],
    ) -> None:
        """Handle shortcut activation."""
        logger.debug(f"Shortcut activated: {shortcut_id} at {timestamp}")

        if shortcut_id in self._shortcuts:
            binding = self._shortcuts[shortcut_id]
            if binding.callback:
                try:
                    binding.callback()
                except Exception as e:
                    logger.error(f"Error in shortcut callback for {shortcut_id}: {e}")

    def _on_shortcut_deactivated(
        self,
        session_handle: str,
        shortcut_id: str,
        timestamp: int,
        options: dict[str, Any],
    ) -> None:
        """Handle shortcut deactivation."""
        logger.debug(f"Shortcut deactivated: {shortcut_id} at {timestamp}")

    def _on_shortcuts_changed(
        self, session_handle: str, shortcuts: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Handle shortcut configuration changes."""
        logger.info(f"Shortcuts changed: {len(shortcuts)} shortcuts")

    def bind_shortcut(
        self, shortcut_id: str, description: str, preferred_trigger: Optional[str] = None
    ) -> bool:
        """
        Bind a keyboard shortcut.

        Args:
            shortcut_id: Unique identifier for the shortcut.
            description: User-readable description of the shortcut.
            preferred_trigger: Preferred key combination (e.g., "<Ctrl><Alt>Space").

        Returns:
            True if the shortcut was successfully bound.
        """
        if not self._session_handle:
            logger.error("No active session")
            return False

        try:
            portal_interface = dbus.Interface(self._portal, self.PORTAL_INTERFACE)

            request_token = self._generate_handle_token("bind")
            request_handle = self._request_handle(request_token)

            # Prepare shortcut data
            shortcut_vardict: dict[str, Any] = {"description": description}
            if preferred_trigger:
                shortcut_vardict["preferred_trigger"] = preferred_trigger

            shortcuts = [(shortcut_id, shortcut_vardict)]

            options = {"handle_token": request_token}

            # Set up response listener
            self._bus.add_signal_receiver(
                self._on_bind_shortcuts_response,
                "Response",
                self.REQUEST_INTERFACE,
                self.PORTAL_BUS_NAME,
                request_handle,
            )

            # Call BindShortcuts
            portal_interface.BindShortcuts(
                self._session_handle,
                shortcuts,
                "",  # parent_window
                options,
                dbus_interface=self.PORTAL_INTERFACE,
            )

            # Wait for response
            self._wait_for_response(timeout=5000)

            return True

        except dbus.DBusException as e:
            logger.error(f"D-Bus error binding shortcut: {e}")
            return False
        except Exception as e:
            logger.error(f"Error binding shortcut: {e}")
            return False

    def _on_bind_shortcuts_response(self, response: int, results: dict[str, Any]) -> None:
        """Handle BindShortcuts response."""
        if response == 0 and "shortcuts" in results:
            bound_shortcuts = results["shortcuts"]
            logger.info(f"Successfully bound {len(bound_shortcuts)} shortcuts")

            for shortcut_id, vardict in bound_shortcuts:
                if shortcut_id in self._shortcuts:
                    binding = self._shortcuts[shortcut_id]
                    binding.trigger = vardict.get("trigger_description")
                    logger.info(
                        f"Shortcut {shortcut_id} bound with trigger: {binding.trigger}"
                    )
        else:
            logger.warning(f"Failed to bind shortcuts: response={response}")

    def list_shortcuts(self) -> list[ShortcutBinding]:
        """List all bound shortcuts."""
        if not self._session_handle:
            return []

        try:
            portal_interface = dbus.Interface(self._portal, self.PORTAL_INTERFACE)

            request_token = self._generate_handle_token("list")
            request_handle = self._request_handle(request_token)

            options = {"handle_token": request_token}

            # Set up response listener
            self._bus.add_signal_receiver(
                self._on_list_shortcuts_response,
                "Response",
                self.REQUEST_INTERFACE,
                self.PORTAL_BUS_NAME,
                request_handle,
            )

            # Call ListShortcuts
            portal_interface.ListShortcuts(
                self._session_handle,
                options,
                dbus_interface=self.PORTAL_INTERFACE,
            )

            # Wait for response
            self._wait_for_response(timeout=5000)

            return list(self._shortcuts.values())

        except Exception as e:
            logger.error(f"Error listing shortcuts: {e}")
            return []

    def _on_list_shortcuts_response(self, response: int, results: dict[str, Any]) -> None:
        """Handle ListShortcuts response."""
        if response == 0 and "shortcuts" in results:
            logger.info(f"Listed {len(results['shortcuts'])} shortcuts")

    def configure_shortcuts(self, parent_window: str = "") -> bool:
        """
        Request configuration UI for shortcuts.

        Args:
            parent_window: Application window identifier.

        Returns:
            True if configuration was requested successfully.
        """
        if not self._session_handle:
            logger.error("No active session")
            return False

        try:
            portal_interface = dbus.Interface(self._portal, self.PORTAL_INTERFACE)

            options = {}

            portal_interface.ConfigureShortcuts(
                self._session_handle,
                parent_window,
                options,
                dbus_interface=self.PORTAL_INTERFACE,
            )

            logger.info("Requested shortcut configuration UI")
            return True

        except Exception as e:
            logger.error(f"Error configuring shortcuts: {e}")
            return False

    def _wait_for_response(self, timeout: int = 5000) -> None:
        """
        Wait for D-Bus response.

        Args:
            timeout: Maximum time to wait in milliseconds.
        """
        if not self._main_loop:
            self._main_loop = GLib.MainLoop()

        # Schedule timeout
        GLib.timeout_add(timeout, self._main_loop.quit)

        try:
            self._main_loop.run()
        except Exception as e:
            logger.debug(f"Error in main loop: {e}")

    def register_callback(
        self, shortcut_id: str, callback: Callable, description: str = ""
    ) -> bool:
        """
        Register a callback for a shortcut.

        Args:
            shortcut_id: Unique identifier for the shortcut.
            callback: Function to call when shortcut is activated.
            description: Description of the shortcut.

        Returns:
            True if successfully registered.
        """
        if shortcut_id not in self._shortcuts:
            self._shortcuts[shortcut_id] = ShortcutBinding(
                shortcut_id=shortcut_id,
                description=description or f"Shortcut {shortcut_id}",
                callback=callback,
            )
            return self.bind_shortcut(
                shortcut_id,
                description or f"Shortcut {shortcut_id}",
            )
        return False

    def start(self) -> bool:
        """
        Start the shortcut session.

        Returns:
            True if successfully started.
        """
        if self._running:
            return True

        if not self.is_available():
            return False

        try:
            self._running = True

            # Create session
            if not self.create_session():
                logger.error("Failed to create shortcut session")
                self._running = False
                return False

            logger.info("Wayland shortcut session started")
            return True

        except Exception as e:
            logger.error(f"Error starting shortcut session: {e}")
            self._running = False
            return False

    def stop(self) -> None:
        """Stop the shortcut session."""
        if not self._running:
            return

        try:
            self._running = False

            if self._main_loop and self._main_loop.is_running():
                self._main_loop.quit()
                self._main_loop = None

            self._shortcuts.clear()
            self._session_handle = None

            logger.info("Wayland shortcut session stopped")

        except Exception as e:
            logger.error(f"Error stopping shortcut session: {e}")


class WaylandQuickLauncher:
    """Quick launcher with Wayland keyboard shortcut support."""

    def __init__(self, shortcut_id: str = "quick_launch", description: str = "Quick Launch"):
        """
        Initialize the quick launcher.

        Args:
            shortcut_id: Unique identifier for the shortcut.
            description: Description shown in the portal UI.
        """
        self.shortcut_id = shortcut_id
        self.description = description
        self.session = WaylandShortcutSession()
        self._on_launch_callback: Optional[Callable] = None

    def set_on_launch(self, callback: Callable) -> None:
        """Set the callback to invoke when shortcut is activated."""
        self._on_launch_callback = callback

    def start(self) -> bool:
        """Start listening for the quick launch shortcut."""
        if not self.session.is_available():
            return False

        if not self.session.start():
            return False

        # Register the quick launch shortcut
        # Common triggers: Super+Space, Ctrl+Alt+Space
        triggers = ["<Super>space", "<Ctrl><Alt>space"]

        for trigger in triggers:
            if self.session.register_callback(
                self.shortcut_id, self._on_activated, self.description
            ):
                logger.info(f"Registered quick launch shortcut with trigger: {trigger}")
                return True

        return False

    def _on_activated(self) -> None:
        """Called when the quick launch shortcut is activated."""
        logger.info("Quick launch shortcut activated")
        if self._on_launch_callback:
            try:
                self._on_launch_callback()
            except Exception as e:
                logger.error(f"Error in on_launch callback: {e}")

    def stop(self) -> None:
        """Stop the quick launcher."""
        self.session.stop()


def is_wayland_available() -> bool:
    """Check if Wayland global shortcuts are available."""
    return WaylandShortcutSession().is_available()
