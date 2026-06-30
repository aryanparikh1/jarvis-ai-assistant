"""
Wake Word Detection
====================
Uses OpenWakeWord to detect "Hey Jarvis" and "Jarvis" wake words.
Runs in a background thread and emits a signal when detected.
"""

import threading
import queue
import numpy as np
from PySide6.QtCore import QObject, Signal
from jarvis.utils.config import config
from jarvis.utils.logger import logger


class WakeWordDetector(QObject):
    """Background thread-based wake word detector using OpenWakeWord."""

    detected = Signal(str)   # Emitted with wake word name
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._thread: threading.Thread | None = None
        self._model = None
        self._model_loaded = False

    def load_model(self):
        """Load the wake word model (call before start)."""
        try:
            from openwakeword.model import Model
            # Use 'hey_jarvis' or custom model if available
            self._model = Model(
                wakeword_models=["hey_jarvis"],
                inference_framework="onnx"
            )
            self._model_loaded = True
            logger.info("Wake word model loaded (hey_jarvis)")
        except ImportError:
            logger.warning("openwakeword not installed — wake word disabled")
        except Exception as e:
            logger.error(f"Wake word model load failed: {e}")
            self.error.emit(str(e))

    def start(self):
        if self._running:
            return
        if not self._model_loaded:
            self.load_model()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Wake word detector started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Wake word detector stopped")

    def _run(self):
        try:
            import sounddevice as sd
            sensitivity = config.get("wake_word_sensitivity", 0.5)
            chunk_size = 1280  # 80ms at 16kHz

            with sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype="int16",
                blocksize=chunk_size,
            ) as stream:
                while self._running:
                    audio_chunk, _ = stream.read(chunk_size)
                    audio_np = np.squeeze(audio_chunk)

                    if self._model:
                        predictions = self._model.predict(audio_np)
                        for ww, score in predictions.items():
                            if score >= sensitivity:
                                logger.info(f"Wake word detected: {ww} (score={score:.3f})")
                                self.detected.emit(ww)
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
            self.error.emit(str(e))
