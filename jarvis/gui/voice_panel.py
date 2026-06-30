"""
Voice Interaction Panel
========================
Full-featured voice panel with:
  - Animated waveform visualizer
  - Wake word status indicator
  - Push-to-talk button
  - STT transcript display
  - TTS status
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot
from PySide6.QtGui import QColor

from jarvis.gui.orb_widget import OrbWidget, OrbState
from jarvis.gui.mic_indicator import MicIndicator, MicState
from jarvis.utils.config import config
from jarvis.utils.logger import logger


class VoicePanel(QWidget):
    """Voice interaction panel — embeddable in the main window."""

    voice_text_ready = Signal(str)       # STT text for chat input
    push_to_talk_pressed = Signal()
    push_to_talk_released = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._voice_active = False
        self._listening = False
        self._wake_word_active = False
        self._build_ui()
        self._start_status_timer()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Orb + status ─────────────────────────────────────────────
        orb_row = QHBoxLayout()
        orb_row.addStretch()
        self.orb = OrbWidget(size=80)
        orb_row.addWidget(self.orb)
        orb_row.addStretch()
        layout.addLayout(orb_row)

        # Status label
        self._status_label = QLabel("Voice Standby")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # ── Wake word toggle ──────────────────────────────────────────
        ww_row = QHBoxLayout()
        self._ww_indicator = QLabel("●")
        self._ww_indicator.setStyleSheet("color: #666; font-size: 10pt;")
        ww_row.addWidget(self._ww_indicator)

        self._ww_label = QLabel(f"Wake word: '{config.get('wake_word', 'hey jarvis')}'")
        self._ww_label.setObjectName("statusLabel")
        ww_row.addWidget(self._ww_label)
        ww_row.addStretch()

        self._ww_toggle = QPushButton("Enable")
        self._ww_toggle.setFixedWidth(72)
        self._ww_toggle.setFixedHeight(28)
        self._ww_toggle.setCheckable(True)
        self._ww_toggle.toggled.connect(self._toggle_wake_word)
        ww_row.addWidget(self._ww_toggle)
        layout.addLayout(ww_row)

        # ── Mic indicator + PTT ───────────────────────────────────────
        ptt_row = QHBoxLayout()
        ptt_row.addStretch()

        self.mic = MicIndicator(size=56)
        self.mic.clicked.connect(self._on_mic_clicked)
        ptt_row.addWidget(self.mic)

        self._ptt_btn = QPushButton("🎤  Hold to Talk")
        self._ptt_btn.setFixedHeight(44)
        self._ptt_btn.setObjectName("primaryBtn")
        self._ptt_btn.pressed.connect(self._ptt_start)
        self._ptt_btn.released.connect(self._ptt_stop)
        ptt_row.addWidget(self._ptt_btn)
        ptt_row.addStretch()
        layout.addLayout(ptt_row)

        # ── Audio level bar ───────────────────────────────────────────
        self._level_bar = QProgressBar()
        self._level_bar.setRange(0, 100)
        self._level_bar.setValue(0)
        self._level_bar.setFixedHeight(4)
        self._level_bar.setTextVisible(False)
        layout.addWidget(self._level_bar)

        # ── Transcript ────────────────────────────────────────────────
        self._transcript = QLabel("Say 'Hey Jarvis' or press Hold to Talk...")
        self._transcript.setWordWrap(True)
        self._transcript.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._transcript.setStyleSheet(
            "color: rgba(255,255,255,0.5); font-size: 9pt; font-style: italic;"
        )
        layout.addWidget(self._transcript)

        layout.addStretch()

    # ── Controls ──────────────────────────────────────────────────────
    def _toggle_wake_word(self, enabled: bool):
        self._wake_word_active = enabled
        self._ww_toggle.setText("Disable" if enabled else "Enable")
        color = "#00D4FF" if enabled else "#666"
        self._ww_indicator.setStyleSheet(f"color: {color}; font-size: 10pt;")
        if enabled:
            self.set_status(OrbState.IDLE, "Listening for wake word...")
            self.mic.set_state(MicState.STANDBY)
        else:
            self.set_status(OrbState.IDLE, "Wake word disabled")
            self.mic.set_state(MicState.OFF)
        logger.info(f"Wake word {'enabled' if enabled else 'disabled'}")

    def _ptt_start(self):
        self._listening = True
        self.set_status(OrbState.LISTENING, "Listening...")
        self.mic.set_state(MicState.SPEECH)
        self.push_to_talk_pressed.emit()

    def _ptt_stop(self):
        self._listening = False
        self.set_status(OrbState.THINKING, "Processing...")
        self.mic.set_state(MicState.STANDBY)
        self.push_to_talk_released.emit()

    def _on_mic_clicked(self):
        if self._listening:
            self._ptt_stop()
        else:
            self._ptt_start()

    def set_status(self, orb_state: OrbState, text: str):
        self.orb.set_state(orb_state)
        self._status_label.setText(text)

    def set_transcript(self, text: str):
        self._transcript.setText(text)

    def set_audio_level(self, level: float):
        self._level_bar.setValue(int(level * 100))
        self.mic.set_audio_level(level)

    def _start_status_timer(self):
        """Simulate audio level for demo (replace with real VAD)."""
        pass
