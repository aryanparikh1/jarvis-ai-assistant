"""
Text-to-Speech Engine
======================
Supports Edge-TTS (Microsoft Neural voices, free) and pyttsx3 (offline fallback).
Runs synthesis in a background thread and plays audio with pygame.
"""

import asyncio
import os
import tempfile
import threading
from PySide6.QtCore import QObject, Signal
from jarvis.utils.config import config
from jarvis.utils.logger import logger


class TTSEngine(QObject):
    """TTS engine with Edge-TTS and pyttsx3 backends."""

    speaking_started = Signal()
    speaking_finished = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._speaking = False
        self._pyttsx3_engine = None
        self._queue: list[str] = []
        self._lock = threading.Lock()

    def speak(self, text: str):
        """Synthesize and play text asynchronously."""
        if not text.strip():
            return
        # Strip markdown
        text = self._clean_text(text)
        thread = threading.Thread(target=self._speak_async, args=(text,), daemon=True)
        thread.start()

    def _speak_async(self, text: str):
        self._speaking = True
        self.speaking_started.emit()
        backend = config.get("tts_backend", "edge")
        try:
            if backend == "edge":
                asyncio.run(self._edge_tts(text))
            else:
                self._pyttsx3_speak(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            self.error.emit(str(e))
        finally:
            self._speaking = False
            self.speaking_finished.emit()

    async def _edge_tts(self, text: str):
        import edge_tts
        voice = config.get("tts_voice", "en-US-AriaNeural")
        rate = config.get("tts_rate", "+0%")
        volume = config.get("tts_volume", "+0%")

        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        await communicate.save(tmp_path)
        self._play_audio(tmp_path)
        os.unlink(tmp_path)

    def _play_audio(self, file_path: str):
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.05)
                if not self._speaking:
                    pygame.mixer.music.stop()
                    break
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def _pyttsx3_speak(self, text: str):
        try:
            import pyttsx3
            if self._pyttsx3_engine is None:
                self._pyttsx3_engine = pyttsx3.init()
                rate = self._pyttsx3_engine.getProperty("rate")
                self._pyttsx3_engine.setProperty("rate", int(rate * 0.95))
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")

    def stop(self):
        """Stop current speech immediately."""
        self._speaking = False
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove markdown formatting for TTS."""
        import re
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', lambda m: m.group(0)[1:-1], text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'•', '', text)
        return text.strip()
