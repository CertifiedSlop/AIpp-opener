"""GUI frontend for AIpp Opener using tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from pathlib import Path
from typing import Optional

from aipp_opener.config import ConfigManager
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.detectors.base import AppDetector
from aipp_opener.ai.ollama import OllamaProvider
from aipp_opener.ai.gemini import GeminiProvider
from aipp_opener.ai.openai import OpenAIProvider
from aipp_opener.ai.openrouter import OpenRouterProvider
from aipp_opener.ai.base import AIProvider
from aipp_opener.ai.nlp import NLPProcessor
from aipp_opener.executor import AppExecutor, ExecutionResult
from aipp_opener.history import HistoryManager
from aipp_opener.voice import VoiceInput


class AppLauncherGUI:
    """GUI application launcher with search and suggestions."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AIpp Opener")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Initialize components
        self.config = ConfigManager()
        self.detector = self._get_detector()
        self.ai_provider = self._get_ai_provider()
        self.executor = AppExecutor(use_notifications=self.config.get().notifications_enabled)
        self.nlp = NLPProcessor()
        self.history = HistoryManager() if self.config.get().history_enabled else None
        self.voice = VoiceInput()

        # Load apps
        self.apps = self.detector.detect()
        self.app_dict = {app.name.lower(): app for app in self.apps}

        # Load favorites
        self.favorites = self._load_favorites()

        # Setup UI
        self._setup_styles()
        self._setup_ui()

        # Bind events
        self.search_entry.bind("<Return>", lambda e: self.launch_selected())
        self.search_entry.bind("<Down>", lambda e: self._navigate_results(1))
        self.search_entry.bind("<Up>", lambda e: self._navigate_results(-1))

        # Focus search on startup
        self.search_entry.focus_set()

        # Update suggestions
        self._update_suggestions("")

    def _get_detector(self) -> AppDetector:
        """Get the appropriate app detector."""
        nixos = NixOSAppDetector()
        if nixos.is_available():
            return nixos
        return DebianAppDetector()

    def _get_ai_provider(self) -> AIProvider:
        """Get the configured AI provider."""
        ai_config = self.config.get().ai

        if ai_config.provider == "ollama":
            return OllamaProvider(
                model=ai_config.model, base_url=ai_config.base_url or "http://localhost:11434"
            )
        elif ai_config.provider == "gemini":
            return GeminiProvider(api_key=ai_config.api_key, model=ai_config.model)
        elif ai_config.provider == "openai":
            return OpenAIProvider(api_key=ai_config.api_key, model=ai_config.model)
        elif ai_config.provider == "openrouter":
            return OpenRouterProvider(api_key=ai_config.api_key, model=ai_config.model)

        return OllamaProvider()

    def _load_favorites(self) -> list[str]:
        """Load favorite apps from config."""
        fav_file = Path.home() / ".config" / "aipp_opener" / "favorites.json"
        if fav_file.exists():
            try:
                with open(fav_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_favorites(self) -> None:
        """Save favorites to config."""
        fav_file = Path.home() / ".config" / "aipp_opener" / "favorites.json"
        fav_file.parent.mkdir(parents=True, exist_ok=True)
        with open(fav_file, "w") as f:
            json.dump(self.favorites, f, indent=2)

    def _setup_styles(self) -> None:
        """Setup ttk styles."""
        style = ttk.Style()

        # Try to use a modern theme
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")
        elif "alt" in available_themes:
            style.theme_use("alt")

        # Configure colors
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=5)

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(header_frame, text="🚀 AIpp Opener", style="Header.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        # Voice button
        self.voice_btn = ttk.Button(
            header_frame, text="🎤 Voice", command=self._toggle_voice, width=10
        )
        self.voice_btn.grid(row=0, column=1, padx=(10, 0))

        self.voice_active = False

        # Search box
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)

        self.search_entry = ttk.Entry(
            search_frame,
            font=("Segoe UI", 14),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_change())

        # Search button
        search_btn = ttk.Button(
            search_frame,
            text="🔍 Search",
            command=lambda: self._update_suggestions(self.search_entry.get()),
        )
        search_btn.grid(row=0, column=1, padx=(5, 0))

        # Favorites section
        fav_frame = ttk.LabelFrame(main_frame, text="⭐ Favorites", padding="5")
        fav_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        fav_frame.columnconfigure(0, weight=1)

        self.favorites_frame = ttk.Frame(fav_frame)
        self.favorites_frame.grid(row=0, column=0, sticky="ew")
        self._update_favorites_display()

        # Results list
        results_frame = ttk.LabelFrame(main_frame, text="📱 Applications", padding="5")
        results_frame.grid(row=3, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Treeview for results
        columns = ("name", "category", "path")
        self.results_tree = ttk.Treeview(
            results_frame, columns=columns, show="headings", selectmode="browse"
        )

        self.results_tree.heading("name", text="Name")
        self.results_tree.heading("category", text="Category")
        self.results_tree.heading("path", text="Path")

        self.results_tree.column("name", width=200, minwidth=150)
        self.results_tree.column("category", width=100, minwidth=80)
        self.results_tree.column("path", width=300, minwidth=200)

        # Scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Bind double-click to launch
        self.results_tree.bind("<Double-1>", lambda e: self.launch_selected())
        self.results_tree.bind("<Return>", lambda e: self.launch_selected())

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        launch_btn = ttk.Button(
            btn_frame,
            text="🚀 Launch Selected",
            command=self.launch_selected,
            style="Accent.TButton",
        )
        launch_btn.pack(side="left", padx=(0, 5))

        fav_btn = ttk.Button(btn_frame, text="⭐ Add to Favorites", command=self.add_to_favorites)
        fav_btn.pack(side="left", padx=(0, 5))

        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_apps)
        refresh_btn.pack(side="left", padx=(0, 5))

        settings_btn = ttk.Button(btn_frame, text="⚙️ Settings", command=self.show_settings)
        settings_btn.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief="sunken", padding=(5, 2)
        )
        status_bar.grid(row=5, column=0, sticky="ew", pady=(5, 0))

    def _update_favorites_display(self) -> None:
        """Update the favorites display."""
        for widget in self.favorites_frame.winfo_children():
            widget.destroy()

        if not self.favorites:
            label = ttk.Label(
                self.favorites_frame,
                text="No favorites yet. Search and add apps!",
                foreground="gray",
            )
            label.pack(pady=5)
            return

        row = 0
        col = 0
        max_cols = 5

        for fav_name in self.favorites[:15]:  # Limit display
            app = self.app_dict.get(fav_name.lower())
            if app:
                btn = ttk.Button(
                    self.favorites_frame,
                    text=app.display_name or app.name,
                    command=lambda a=app: self.launch_app(a),
                    width=15,
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="w")

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def _on_search_change(self) -> None:
        """Handle search text change."""
        query = self.search_entry.get()
        self._update_suggestions(query)

    def _update_suggestions(self, query: str) -> None:
        """Update suggestions based on query."""
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        if not query.strip():
            # Show frequent apps
            if self.history:
                frequent = self.history.get_frequent_apps(20)
                for freq in frequent:
                    app = self.app_dict.get(freq["app_name"].lower())
                    if app:
                        self._add_app_to_tree(app)
            else:
                # Show first 50 apps
                for app in self.apps[:50]:
                    self._add_app_to_tree(app)
            return

        # Use NLP to find matches
        extracted = self.nlp.extract_app_intent(query)
        app_names = [app.name for app in self.apps]

        matches = self.nlp.find_all_matches(extracted, app_names, min_score=40)

        for name, _score in matches[:50]:
            app = self.app_dict.get(name.lower())
            if app:
                self._add_app_to_tree(app)

        self.status_var.set(f"Found {len(matches)} matches")

    def _add_app_to_tree(self, app) -> None:
        """Add an app to the results tree."""
        category = app.categories[0] if app.categories else "Other"
        self.results_tree.insert(
            "",
            "end",
            values=(app.display_name or app.name, category, app.executable),
            tags=(app.name.lower(),),
        )

    def _navigate_results(self, direction: int) -> None:
        """Navigate through results with keyboard."""
        selected = self.results_tree.selection()
        if selected:
            current = selected[0]
            next_item = (
                self.results_tree.next(current)
                if direction > 0
                else self.results_tree.prev(current)
            )
            if next_item:
                self.results_tree.selection_set(next_item)
                self.results_tree.focus(next_item)
        else:
            first = self.results_tree.get_children()
            if first:
                self.results_tree.selection_set(first[0])
                self.results_tree.focus(first[0])

    def launch_selected(self) -> None:
        """Launch the selected application."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an application to launch.")
            return

        item = self.results_tree.item(selection[0])
        app_name = item["values"][0]
        executable = item["values"][2]

        # Find the app object
        app = None
        for a in self.apps:
            if a.executable == executable or a.name == app_name:
                app = a
                break

        if app:
            self.launch_app(app)

    def launch_app(self, app) -> None:
        """Launch an application."""
        self.status_var.set(f"Launching {app.display_name or app.name}...")
        self.root.update()

        def run_launch():
            result = self.executor.execute(app.executable)

            if self.history and result.success:
                self.history.record(app.display_name or app.name, app.name, app.executable)

            # Update status in main thread
            self.root.after(0, lambda: self._on_launch_complete(result))

        thread = threading.Thread(target=run_launch, daemon=True)
        thread.start()

    def _on_launch_complete(self, result: ExecutionResult) -> None:
        """Handle launch completion."""
        if result.success:
            self.status_var.set(f"✓ Launched: {result.app_name}")
        else:
            self.status_var.set(f"✗ Failed: {result.message}")
            messagebox.showerror("Launch Failed", result.message)

    def add_to_favorites(self) -> None:
        """Add selected app to favorites."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection", "Please select an application to add to favorites."
            )
            return

        item = self.results_tree.item(selection[0])
        app_name = item["values"][0]

        # Find the app key
        for key, app in self.app_dict.items():
            if app.display_name == app_name or app.name == app_name:
                if key not in self.favorites:
                    self.favorites.append(key)
                    self._save_favorites()
                    self._update_favorites_display()
                    self.status_var.set(f"Added {app_name} to favorites")
                else:
                    self.status_var.set(f"{app_name} is already in favorites")
                return

    def remove_from_favorites(self, app_name: str) -> None:
        """Remove an app from favorites."""
        if app_name in self.favorites:
            self.favorites.remove(app_name)
            self._save_favorites()
            self._update_favorites_display()

    def refresh_apps(self) -> None:
        """Refresh the app list."""
        self.status_var.set("Refreshing app list...")
        self.root.update()

        def run_refresh():
            self.detector.refresh()
            self.apps = self.detector.detect()
            self.app_dict = {app.name.lower(): app for app in self.apps}

            # Update in main thread
            self.root.after(0, self._on_refresh_complete)

        thread = threading.Thread(target=run_refresh, daemon=True)
        thread.start()

    def _on_refresh_complete(self) -> None:
        """Handle refresh completion."""
        self.status_var.set(f"Loaded {len(self.apps)} applications")
        self._update_suggestions(self.search_entry.get())

    def _toggle_voice(self) -> None:
        """Toggle voice input mode."""
        if not self.voice.is_available():
            messagebox.showerror(
                "Voice Not Available",
                "Voice input is not available. Make sure SpeechRecognition is installed.",
            )
            return

        if self.voice_active:
            self.voice.stop_listening()
            self.voice_active = False
            self.voice_btn.configure(text="🎤 Voice")
            self.status_var.set("Voice input stopped")
        else:
            self.status_var.set("Listening... Speak now")
            self.voice_btn.configure(text="⏹ Stop")
            self.voice_active = True

            def on_recognized(text: str):
                self.root.after(0, lambda: self._on_voice_recognized(text))

            def listen_thread():
                text = self.voice.listen_once()
                if text:
                    on_recognized(text)
                self.root.after(0, self._stop_voice)

            thread = threading.Thread(target=listen_thread, daemon=True)
            thread.start()

    def _stop_voice(self) -> None:
        """Stop voice input."""
        self.voice_active = False
        self.voice_btn.configure(text="🎤 Voice")

    def _on_voice_recognized(self, text: str) -> None:
        """Handle voice recognition result."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
        self._update_suggestions(text)
        self.status_var.set(f"Recognized: {text}")

    def show_settings(self) -> None:
        """Show settings dialog."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("500x400")
        settings_win.transient(self.root)
        settings_win.grab_set()

        # Create notebook
        notebook = ttk.Notebook(settings_win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # AI Settings tab
        ai_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ai_frame, text="AI Provider")

        ttk.Label(ai_frame, text="Provider:").grid(row=0, column=0, sticky="w", pady=5)
        provider_var = tk.StringVar(value=self.config.get().ai.provider)
        provider_combo = ttk.Combobox(
            ai_frame,
            textvariable=provider_var,
            values=["ollama", "gemini", "openai", "openrouter"],
            state="readonly",
            width=30,
        )
        provider_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Label(ai_frame, text="Model:").grid(row=1, column=0, sticky="w", pady=5)
        model_entry = ttk.Entry(ai_frame, width=35)
        model_entry.insert(0, self.config.get().ai.model)
        model_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Label(ai_frame, text="API Key:").grid(row=2, column=0, sticky="w", pady=5)
        api_entry = ttk.Entry(ai_frame, width=35, show="*")
        if self.config.get().ai.api_key:
            api_entry.insert(0, self.config.get().ai.api_key)
        api_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))

        ttk.Label(ai_frame, text="Base URL:").grid(row=3, column=0, sticky="w", pady=5)
        url_entry = ttk.Entry(ai_frame, width=35)
        if self.config.get().ai.base_url:
            url_entry.insert(0, self.config.get().ai.base_url)
        url_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))

        # General Settings tab
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="General")

        notifications_var = tk.BooleanVar(value=self.config.get().notifications_enabled)
        ttk.Checkbutton(
            general_frame, text="Enable notifications", variable=notifications_var
        ).grid(row=0, column=0, sticky="w", pady=5)

        history_var = tk.BooleanVar(value=self.config.get().history_enabled)
        ttk.Checkbutton(general_frame, text="Enable history", variable=history_var).grid(
            row=1, column=0, sticky="w", pady=5
        )

        ttk.Label(general_frame, text="Max suggestions:").grid(row=2, column=0, sticky="w", pady=5)
        max_spin = ttk.Spinbox(general_frame, from_=1, to=10, width=5)
        max_spin.set(self.config.get().max_suggestions)
        max_spin.grid(row=2, column=0, sticky="e", padx=(200, 0), pady=5)

        # Save button
        def save_settings():
            self.config.update(
                provider=provider_var.get(),
                model=model_entry.get().strip(),
                api_key=api_entry.get().strip() or None,
                base_url=url_entry.get().strip() or None,
                notifications_enabled=notifications_var.get(),
                history_enabled=history_var.get(),
                max_suggestions=int(max_spin.get()),
            )
            # Reload AI provider
            self.ai_provider = self._get_ai_provider()
            self.executor = AppExecutor(use_notifications=notifications_var.get())
            if history_var.get() and not self.history:
                self.history = HistoryManager()
            elif not history_var.get() and self.history:
                self.history = None

            settings_win.destroy()
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")

        btn_frame = ttk.Frame(settings_win)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Save", command=save_settings).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=settings_win.destroy).pack(side="right")


def main():
    """Main entry point for GUI."""
    root = tk.Tk()

    # Set window icon (if available)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = AppLauncherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
