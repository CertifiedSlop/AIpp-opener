"""Tests for voice module (Phase 8)."""

import unittest
from unittest.mock import patch, MagicMock


class TestVoiceInput(unittest.TestCase):
    """Tests for VoiceInput class."""

    def test_voice_init(self):
        """Test VoiceInput initialization."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        self.assertIsNotNone(voice)
        self.assertIsNone(voice.recognizer)
        self.assertIsNone(voice.microphone)
        self.assertFalse(voice._is_listening)
        self.assertIsNone(voice._listen_thread)

    def test_voice_not_available_no_library(self):
        """Test voice is not available without library."""
        with patch('aipp_opener.voice.VOICE_AVAILABLE', False):
            from aipp_opener.voice import VoiceInput
            voice = VoiceInput()
            self.assertFalse(voice.is_available())

    def test_voice_available(self):
        """Test voice availability check."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        # May return True or False depending on system
        result = voice.is_available()
        self.assertIsInstance(result, bool)

    def test_listen_once_not_available(self):
        """Test listen_once when voice not available."""
        with patch('aipp_opener.voice.VOICE_AVAILABLE', False):
            from aipp_opener.voice import VoiceInput
            voice = VoiceInput()
            result = voice.listen_once()
            self.assertIsNone(result)

    def test_is_listening_false(self):
        """Test is_listening returns False when not listening."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        self.assertFalse(voice.is_listening())

    def test_stop_listening(self):
        """Test stop_listening method."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        # Should not raise
        voice.stop_listening()

    def test_list_microphones(self):
        """Test list_microphones method."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        # Should return a list (may be empty)
        mics = voice.list_microphones()
        self.assertIsInstance(mics, list)


class TestVoiceInputContinuous(unittest.TestCase):
    """Tests for VoiceInput continuous listening."""

    def test_listen_continuous_callback(self):
        """Test listen_continuous callback function."""
        from aipp_opener.voice import VoiceInput
        
        callback_called = []
        def test_callback(text):
            callback_called.append(text)
        
        voice = VoiceInput()
        # Should not raise
        voice.listen_continuous(test_callback)

    def test_listen_continuous_no_callback(self):
        """Test listen_continuous without callback."""
        from aipp_opener.voice import VoiceInput
        voice = VoiceInput()
        # Should not raise
        voice.listen_continuous(None)


if __name__ == "__main__":
    unittest.main()
