"""System tray integration for AIpp Opener."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys

try:
    import pystray
    from pystray import Icon, MenuItem, Menu
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

from aipp_opener.config import ConfigManager
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.executor import AppExecutor
from aipp_opener.history import HistoryManager


def create_icon_image():
    """Create a simple icon image for the tray."""
    size = (64, 64)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a rocket shape (simplified)
    # Body
    draw.ellipse([16, 16, 48, 48], fill='#4CAF50', outline='#2E7D32', width=2)
    # Window
    draw.ellipse([24, 24, 40, 40], fill='#81C784', outline='#2E7D32', width=1)
    # Flame
    draw.polygon([(32, 48), (24, 60), (40, 60)], fill='#FF9800', outline='#F57C00')
    
    return image


class TrayApp:
    """System tray application for AIpp Opener."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.detector = self._get_detector()
        self.executor = AppExecutor(use_notifications=self.config.get().notifications_enabled)
        self.nlp = NLPProcessor()
        self.history = HistoryManager() if self.config.get().history_enabled else None
        
        self.apps = self.detector.detect()
        self.app_dict = {app.name.lower(): app for app in self.apps}
        
        self.icon = None
        self._popup = None
    
    def _get_detector(self):
        """Get the appropriate app detector."""
        nixos = NixOSAppDetector()
        if nixos.is_available():
            return nixos
        return DebianAppDetector()
    
    def _create_menu(self):
        """Create the tray menu."""
        # Get frequent apps
        frequent = []
        if self.history:
            freq_apps = self.history.get_frequent_apps(5)
            frequent = [
                MenuItem(
                    f['app_name'],
                    lambda _, app=f['app_name']: self._launch_by_name(app),
                    enabled=True
                )
                for f in freq_apps
            ]
        
        if not frequent:
            frequent = [MenuItem("No frequent apps", None, enabled=False)]
        
        return Menu(
            MenuItem("🚀 AIpp Opener", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("📊 Frequent Apps", Menu(*frequent)),
            MenuItem("🔍 Search...", self._show_search),
            MenuItem("📱 All Apps", self._show_all_apps),
            Menu.SEPARATOR,
            MenuItem("⚙️ Settings", self._show_settings),
            MenuItem("📈 Statistics", self._show_stats),
            Menu.SEPARATOR,
            MenuItem("❌ Quit", self._quit)
        )
    
    def _launch_by_name(self, name: str):
        """Launch an app by name."""
        app = self.app_dict.get(name.lower())
        if app:
            self.executor.execute(app.executable)
            if self.history:
                self.history.record(name, app.name, app.executable)
    
    def _show_search(self, icon, item):
        """Show search dialog."""
        self._create_popup("Search Apps", self._search_ui)
    
    def _search_ui(self, frame):
        """Create search UI."""
        ttk.Label(frame, text="Search for an app:").pack(pady=(0, 5))
        
        entry = ttk.Entry(frame, width=40)
        entry.pack(pady=(0, 10))
        entry.focus_set()
        
        results_frame = ttk.LabelFrame(frame, text="Results")
        results_frame.pack(fill="both", expand=True)
        
        listbox = tk.Listbox(results_frame, width=40, height=10)
        listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        
        def update_results(event=None):
            query = entry.get()
            listbox.delete(0, 'end')
            
            if query:
                extracted = self.nlp.extract_app_intent(query)
                app_names = [app.name for app in self.apps]
                matches = self.nlp.find_all_matches(extracted, app_names, min_score=40)
                
                for name, score in matches[:20]:
                    app = self.app_dict.get(name.lower())
                    if app:
                        display = app.display_name or app.name
                        listbox.insert('end', f"{display} ({name})")
        
        def on_select(event=None):
            selection = listbox.curselection()
            if selection:
                item = listbox.get(selection[0])
                # Extract app name from display
                name = item.split('(')[1].rstrip(')') if '(' in item else item
                self._launch_by_name(name)
                self._close_popup()
        
        entry.bind('<KeyRelease>', update_results)
        entry.bind('<Return>', on_select)
        listbox.bind('<Double-Button-1>', on_select)
        
        ttk.Button(frame, text="Close", command=self._close_popup).pack(pady=(10, 0))
    
    def _show_all_apps(self, icon, item):
        """Show all apps window."""
        self._create_popup("All Applications", self._all_apps_ui)
    
    def _all_apps_ui(self, frame):
        """Create all apps UI."""
        ttk.Label(frame, text=f"Installed Applications ({len(self.apps)})").pack(pady=(0, 10))
        
        # Search filter
        filter_entry = ttk.Entry(frame, width=40)
        filter_entry.pack(pady=(0, 10))
        
        # Scrollable list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(list_frame, width=50, height=20, yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        # Insert apps
        for app in sorted(self.apps, key=lambda a: a.display_name or a.name):
            name = app.display_name or app.name
            text.insert('end', f"{name}\n", (app.name,))
            text.tag_bind(
                app.name,
                '<Double-1>',
                lambda e, a=app: (self._launch_by_name(a.name), self._close_popup())
            )
            text.tag_config(app.name, foreground='blue', underline=True)
        
        def filter_apps(event=None):
            query = filter_entry.get().lower()
            text.delete('1.0', 'end')
            
            for app in self.apps:
                name = (app.display_name or app.name).lower()
                if query in name or query in app.name.lower():
                    display = app.display_name or app.name
                    text.insert('end', f"{display}\n", (app.name,))
                    text.tag_bind(
                        app.name,
                        '<Double-1>',
                        lambda e, a=app: (self._launch_by_name(a.name), self._close_popup())
                    )
                    text.tag_config(app.name, foreground='blue', underline=True)
        
        filter_entry.bind('<KeyRelease>', filter_apps)
        
        ttk.Button(frame, text="Close", command=self._close_popup).pack(pady=(10, 0))
    
    def _show_settings(self, icon, item):
        """Show settings dialog."""
        self._create_popup("Settings", self._settings_ui)
    
    def _settings_ui(self, frame):
        """Create settings UI."""
        config = self.config.get()
        
        # AI Provider
        ai_frame = ttk.LabelFrame(frame, text="AI Provider")
        ai_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(ai_frame, text=f"Current: {config.ai.provider}").pack(pady=2)
        ttk.Label(ai_frame, text=f"Model: {config.ai.model}").pack(pady=2)
        
        # General
        gen_frame = ttk.LabelFrame(frame, text="General")
        gen_frame.pack(fill="x", padx=10, pady=5)
        
        notif_var = tk.BooleanVar(value=config.notifications_enabled)
        ttk.Checkbutton(gen_frame, text="Notifications", variable=notif_var).pack(anchor="w")
        
        hist_var = tk.BooleanVar(value=config.history_enabled)
        ttk.Checkbutton(gen_frame, text="History", variable=hist_var).pack(anchor="w")
        
        def save():
            self.config.update(
                notifications_enabled=notif_var.get(),
                history_enabled=hist_var.get()
            )
            self.executor = AppExecutor(use_notifications=notif_var.get())
            if hist_var.get() and not self.history:
                self.history = HistoryManager()
            elif not hist_var.get() and self.history:
                self.history = None
            messagebox.showinfo("Settings", "Settings saved!")
        
        ttk.Button(frame, text="Save", command=save).pack(pady=10)
        ttk.Button(frame, text="Close", command=self._close_popup).pack()
    
    def _show_stats(self, icon, item):
        """Show statistics."""
        self._create_popup("Usage Statistics", self._stats_ui)
    
    def _stats_ui(self, frame):
        """Create stats UI."""
        if self.history:
            stats = self.history.get_stats()
            
            text = tk.Text(frame, width=50, height=15)
            text.pack(fill="both", expand=True, padx=10, pady=10)
            
            text.insert('1.0', f"""
Usage Statistics
================

Total Launches: {stats['total_launches']}
Successful: {stats['successful_launches']}
Failed: {stats['failed_launches']}
Unique Apps: {stats['unique_apps']}
Most Used: {stats['most_used_app'] or 'N/A'}

Frequent Apps:
""")
            
            for i, app in enumerate(self.history.get_frequent_apps(10), 1):
                text.insert('end', f"  {i}. {app['app_name']}: {app['count']} times\n")
            
            text.config(state='disabled')
        else:
            ttk.Label(frame, text="History is disabled").pack(pady=20)
        
        ttk.Button(frame, text="Close", command=self._close_popup).pack(pady=10)
    
    def _create_popup(self, title: str, content_func):
        """Create a popup window."""
        if self._popup:
            self._popup.destroy()
        
        self._popup = tk.Toplevel()
        self._popup.title(title)
        self._popup.geometry("500x400")
        self._popup.resizable(True, True)
        
        # Center on screen
        self._popup.update_idletasks()
        x = (self._popup.winfo_screenwidth() // 2) - 250
        y = (self._popup.winfo_screenheight() // 2) - 200
        self._popup.geometry(f"+{x}+{y}")
        
        container = ttk.Frame(self._popup, padding="10")
        container.pack(fill="both", expand=True)
        
        content_func(container)
    
    def _close_popup(self):
        """Close the popup window."""
        if self._popup:
            self._popup.destroy()
            self._popup = None
    
    def _quit(self, icon, item):
        """Quit the application."""
        if self.icon:
            self.icon.stop()
    
    def run(self):
        """Run the tray application."""
        if not PYSTRAY_AVAILABLE:
            print("pystray not available. Install with: pip install pystray pillow")
            print("Falling back to minimal tray mode...")
            self._run_fallback()
            return
        
        image = create_icon_image()
        
        self.icon = Icon(
            "aipp-opener",
            image,
            "AIpp Opener",
            self._create_menu()
        )
        
        self.icon.run()
    
    def _run_fallback(self):
        """Run a minimal tkinter-based tray alternative."""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        # Create a small status window
        status = tk.Toplevel(root)
        status.title("AIpp Opener")
        status.geometry("300x150")
        
        ttk.Label(
            status,
            "AIpp Opener\n\nSystem tray not available.\nUse --gui for full interface.",
            justify="center"
        ).pack(expand=True)
        
        ttk.Button(status, text="Open GUI", command=lambda: (
            status.destroy(),
            root.destroy(),
            self._launch_gui()
        )).pack(pady=10)
        
        ttk.Button(status, text="Quit", command=lambda: (
            status.destroy(),
            root.destroy()
        )).pack()
        
        status.protocol("WM_DELETE_WINDOW", lambda: (status.destroy(), root.destroy()))
        root.mainloop()
    
    def _launch_gui(self):
        """Launch the GUI."""
        from aipp_opener.gui import main as gui_main
        gui_main()


def main():
    """Main entry point for tray mode."""
    app = TrayApp()
    app.run()


if __name__ == "__main__":
    main()
