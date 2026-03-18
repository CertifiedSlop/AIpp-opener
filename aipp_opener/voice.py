"""Voice input module for AIpp Opener."""

import threading
from typing import Optional, Callable

try:
    import speech_recognition as sr

    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


class VoiceInput:
    """Handles voice input using speech recognition."""

    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self._is_listening = False
        self._listen_thread: Optional[threading.Thread] = None

    def is_available(self) -> bool:
        """Check if voice input is available."""
        if not VOICE_AVAILABLE:
            return False

        try:
            self._init_recognizer()
            return self.recognizer is not None
        except Exception:
            return False

    def _init_recognizer(self) -> None:
        """Initialize the speech recognizer."""
        if self.recognizer is None:
            self.recognizer = sr.Recognizer()

            # Adjust recognizer settings
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

        if self.microphone is None:
            try:
                self.microphone = sr.Microphone()
            except (OSError, IOError):
                self.microphone = None

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for a single voice command.

        Args:
            timeout: Timeout in seconds.

        Returns:
            Recognized text or None.
        """
        if not self.is_available():
            return None

        self._init_recognizer()

        if self.microphone is None:
            return None

        try:
            with self.microphone as source:
                print("Listening... (speak now)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)

            # Try Google Speech Recognition (free, no API key needed)
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            print("No speech detected")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            return None
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return None

    def listen_continuous(
        self,
        callback: Callable[[str], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        Start continuous listening in a background thread.

        Args:
            callback: Function to call with recognized text.
            on_error: Optional function to call on errors.
        """
        if not self.is_available():
            return

        self._is_listening = True

        def _listen_loop():
            self._init_recognizer()

            if self.microphone is None:
                return

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("Continuous listening started...")

                while self._is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=10)
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            callback(text.lower())
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        if on_error:
                            on_error(e)
                    except Exception as e:
                        if on_error:
                            on_error(e)

        self._listen_thread = threading.Thread(target=_listen_loop, daemon=True)
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop continuous listening."""
        self._is_listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=2)
            self._listen_thread = None

    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening

    def list_microphones(self) -> list[dict]:
        """List available microphones."""
        if not VOICE_AVAILABLE:
            return []

        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []
