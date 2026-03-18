"""Global keyboard shortcut support for AIpp Opener."""

import threading
import subprocess
import sys
from typing import Optional, Callable

try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import Xlib.display
    import Xlib.ext.xtest
    import Xlib.X
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False


class KeyboardShortcut:
    """Global keyboard shortcut handler."""

    def __init__(self, shortcut: str = "<ctrl><alt>space"):
        """
        Initialize keyboard shortcut handler.

        Args:
            shortcut: Key combination string (e.g., "<ctrl><alt>space")
        """
        self.shortcut = shortcut
        self.callback: Optional[Callable] = None
        self.listener: Optional[keyboard.Listener] = None
        self._pressed = set()
        self._running = False

    def is_available(self) -> bool:
        """Check if keyboard shortcuts are available."""
        return KEYBOARD_AVAILABLE

    def parse_shortcut(self, shortcut: str) -> set:
        """
        Parse shortcut string into key set.

        Args:
            shortcut: Key combination string.

        Returns:
            Set of key codes.
        """
        keys = set()
        parts = shortcut.lower().replace(">", "").split("<")

        key_map = {
            "ctrl": keyboard.Key.ctrl,
            "alt": keyboard.Key.alt,
            "shift": keyboard.Key.shift,
            "super": keyboard.Key.cmd,
            "cmd": keyboard.Key.cmd,
            "win": keyboard.Key.cmd,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "escape": keyboard.Key.esc,
            "tab": keyboard.Key.tab,
        }

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part in key_map:
                keys.add(key_map[part])
            elif len(part) == 1:
                keys.add(part)
            else:
                # Try to map to keyboard.KeyCode
                try:
                    keys.add(keyboard.KeyCode.from_char(part[0]))
                except ValueError:
                    pass

        return keys

    def start(self, callback: Callable) -> None:
        """
        Start listening for keyboard shortcuts.

        Args:
            callback: Function to call when shortcut is pressed.
        """
        if not self.is_available():
            print("Keyboard shortcuts not available. Install pynput.")
            return

        self.callback = callback
        self._running = True

        required_keys = self.parse_shortcut(self.shortcut)

        def on_press(key):
            self._pressed.add(key)

            # Check if all required keys are pressed
            if all(k in self._pressed for k in required_keys):
                if self.callback:
                    # Run callback in separate thread to avoid blocking
                    threading.Thread(target=self.callback, daemon=True).start()

        def on_release(key):
            try:
                self._pressed.remove(key)
            except KeyError:
                pass

            # Stop listener if escape is pressed
            if key == keyboard.Key.esc:
                return False

        self.listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.listener.start()

    def stop(self) -> None:
        """Stop listening for keyboard shortcuts."""
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None


class QuickLauncher:
    """Quick launcher popup with keyboard shortcut."""

    def __init__(
        self,
        shortcut: str = "<ctrl><alt>space",
        on_launch: Optional[Callable] = None
    ):
        """
        Initialize quick launcher.

        Args:
            shortcut: Keyboard shortcut to trigger launcher.
            on_launch: Callback when app is launched.
        """
        self.shortcut = shortcut
        self.on_launch = on_launch
        self.keyboard = KeyboardShortcut(shortcut)
        self._popup = None

    def show_popup(self) -> None:
        """Show the quick launch popup."""
        import tkinter as tk
        from tkinter import ttk

        from aipp_opener.detectors.nixos import NixOSAppDetector
        from aipp_opener.detectors.debian import DebianAppDetector
        from aipp_opener.ai.nlp import NLPProcessor
        from aipp_opener.executor import AppExecutor
        from aipp_opener.history import HistoryManager

        # Get detector
        nixos = NixOSAppDetector()
        detector = nixos if nixos.is_available() else DebianAppDetector()
        apps = detector.detect()
        app_dict = {app.name.lower(): app for app in apps}

        nlp = NLPProcessor()
        executor = AppExecutor()
        history = HistoryManager()

        # Create popup
        self._popup = tk.Toplevel()
        self._popup.title("Quick Launch")
        self._popup.geometry("500x300")

        # Always on top
        self._popup.attributes('-topmost', True)

        # Center on screen
        self._popup.update_idletasks()
        x = (self._popup.winfo_screenwidth() // 2) - 250
        y = 100  # Top of screen
        self._popup.geometry(f"+{x}+{y}")

        # Remove window decorations
        self._popup.overrideredirect(True)

        # Search entry
        entry = ttk.Entry(self._popup, font=('Segoe UI', 14))
        entry.pack(fill="x", padx=10, pady=10)
        entry.focus_set()

        # Results listbox
        listbox = tk.Listbox(self._popup, font=('Segoe UI', 11), height=10)
        listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Scrollbar
        scrollbar = ttk.Scrollbar(self._popup, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        def update_results(query: str = ""):
            listbox.delete(0, 'end')

            if not query:
                # Show frequent apps
                if history:
                    for freq in history.get_frequent_apps(10):
                        listbox.insert('end', f"⭐ {freq['app_name']}")
                return

            extracted = nlp.extract_app_intent(query)
            app_names = [app.name for app in apps]
            matches = nlp.find_all_matches(extracted, app_names, min_score=40)

            for name, score in matches[:15]:
                app = app_dict.get(name.lower())
                if app:
                    display = app.display_name or app.name
                    listbox.insert('end', display)

        def launch_selected(event=None):
            selection = listbox.curselection()
            if selection:
                item = listbox.get(selection[0])
                # Remove star prefix
                if item.startswith("⭐ "):
                    item = item[2:]

                # Find and launch app
                for app in apps:
                    if (app.display_name or app.name) == item:
                        executor.execute(app.executable)
                        if history:
                            history.record(item, app.name, app.executable)
                        if self.on_launch:
                            self.on_launch(app)
                        break

                close_popup()

        def close_popup():
            if self._popup:
                self._popup.destroy()
                self._popup = None

        entry.bind('<KeyRelease>', lambda e: update_results(entry.get()))
        entry.bind('<Return>', launch_selected)
        entry.bind('<Escape>', lambda e: close_popup())
        listbox.bind('<Double-Button-1>', launch_selected)
        listbox.bind('<Return>', launch_selected)

        # Initial display
        update_results()

        # Close on focus loss
        def on_focus_out(event):
            self._popup.after(200, lambda: close_popup())

        self._popup.bind('<FocusOut>', on_focus_out)

    def start(self) -> None:
        """Start the quick launcher."""
        self.keyboard.start(self.show_popup)

    def stop(self) -> None:
        """Stop the quick launcher."""
        self.keyboard.stop()


def simulate_keypress(keysym: str) -> None:
    """
    Simulate a keypress using X11.

    Args:
        keysym: X11 keysym name (e.g., "space", "Return").
    """
    if not XLIB_AVAILABLE:
        return

    try:
        display = Xlib.display.Display()
        window = display.screen().root

        # Get keycode for keysym
        keysym_code = getattr(Xlib.X, f'XK_{keysym}', None)
        if keysym_code is None:
            return

        keycode = display.keysym_to_keycode(keysym_code)

        # Press and release
        Xlib.ext.xtest.fake_input(display, Xlib.X.KeyPress, keycode)
        Xlib.ext.xtest.fake_input(display, Xlib.X.KeyRelease, keycode)
        display.sync()
    except Exception:
        pass


def main():
    """Run keyboard shortcut demo."""
    print("AIpp Opener - Keyboard Shortcut Demo")
    print("=====================================")
    print("Press Ctrl+Alt+Space to open quick launcher")
    print("Press Escape to exit")
    print()

    if not KeyboardShortcut().is_available():
        print("pynput not available. Install with: pip install pynput")
        return

    launcher = QuickLauncher(shortcut="<ctrl><alt>space")
    launcher.start()

    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        launcher.stop()
        print("\nExiting...")


if __name__ == "__main__":
    main()
