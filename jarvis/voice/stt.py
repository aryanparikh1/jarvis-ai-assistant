"""
Speech-to-Text Engine
======================
Supports faster-whisper (local, default) and Google STT (online fallback).
"""

import os
import tempfile
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6.QtCore import QObject, Signal, QThread
from jarvis.utils.config import config
from jarvis.utils.logger import logger


class STTEngine(QObject):
    """
    Records audio and transcribes it to text.
    Supports:
      - faster-whisper (local, high accuracy)
      - Google SpeechRecognition (online, fast)
    """

    transcription_ready = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal()
    error = Signal(str)
    audio_level = Signal(float)  # 0..1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._whisper_model = None
        self._is_recording = False
        self._recorded_frames: list[np.ndarray] = []
        self._record_thread: threading.Thread | None = None
        self._sample_rate = 16000

    def load_whisper(self):
        """Lazy-load the Whisper model."""
        if self._whisper_model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            model_size = config.get("whisper_model", "base")
            logger.info(f"Loading Whisper model: {model_size}")
            self._whisper_model = WhisperModel(
                model_size,
                device="auto",
                compute_type="int8"
            )
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("faster-whisper not installed")
        except Exception as e:
            logger.error(f"Whisper load error: {e}")
            self.error.emit(str(e))

    def start_recording(self):
        """Begin capturing microphone audio."""
        if self._is_recording:
            return
        self._is_recording = True
        self._recorded_frames = []
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()
        self.recording_started.emit()
        logger.debug("Recording started")

    def stop_recording_and_transcribe(self):
        """Stop recording and run STT."""
        self._is_recording = False
        if self._record_thread:
            self._record_thread.join(timeout=3)
        self.recording_stopped.emit()
        logger.debug("Recording stopped, transcribing...")

        if not self._recorded_frames:
            self.transcription_ready.emit("")
            return

        audio = np.concatenate(self._recorded_frames, axis=0).flatten()

        backend = config.get("stt_backend", "whisper")
        if backend == "whisper":
            self._transcribe_whisper(audio)
        else:
            self._transcribe_google(audio)

    def _record_loop(self):
        chunk_size = 1024
        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            blocksize=chunk_size,
        ) as stream:
            while self._is_recording:
                chunk, _ = stream.read(chunk_size)
                self._recorded_frames.append(chunk.copy())
                # Compute RMS for level meter
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                self.audio_level.emit(min(1.0, rms * 10))

    def _transcribe_whisper(self, audio: np.ndarray):
        if self._whisper_model is None:
            self.load_whisper()
        if self._whisper_model is None:
            self.error.emit("Whisper model not available")
            return
        try:
            # Save to temp WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
            sf.write(tmp_path, audio, self._sample_rate)
            segments, info = self._whisper_model.transcribe(
                tmp_path, beam_size=5, language="en"
            )
            text = " ".join(seg.text.strip() for seg in segments)
            os.unlink(tmp_path)
            logger.info(f"Whisper STT: '{text}'")
            self.transcription_ready.emit(text.strip())
        except Exception as e:
            logger.error(f"Whisper STT error: {e}")
            self.error.emit(str(e))

    def _transcribe_google(self, audio: np.ndarray):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            # Convert float32 to int16 for SpeechRecognition
            audio_int16 = (audio * 32767).astype(np.int16)
            audio_data = sr.AudioData(
                audio_int16.tobytes(), self._sample_rate, 2
            )
            text = recognizer.recognize_google(audio_data)
            logger.info(f"Google STT: '{text}'")
            self.transcription_ready.emit(text.strip())
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            self.error.emit(str(e))
