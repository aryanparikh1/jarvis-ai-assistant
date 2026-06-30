"""
Developer Console Window
=========================
Live log viewer with color-coded log levels, filter, and clear controls.
Intercepts the loguru logger and streams to the UI.
"""

import re
from collections import deque

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QComboBox, QLabel, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont

from jarvis.utils.logger import logger


class LogSignalEmitter(QObject):
    """Thread-safe bridge to emit log records into the Qt event loop."""
    log_received = Signal(str, str)  # level, message


_emitter = LogSignalEmitter()


def _qt_log_sink(message):
    """Custom loguru sink that emits into the Qt signal."""
    record = message.record
    level = record["level"].name
    text = record["message"]
    time_str = record["time"].strftime("%H:%M:%S.%f")[:-3]
    func = f'{record["name"]}:{record["function"]}:{record["line"]}'
    formatted = f"[{time_str}] [{level:<8}] {func} — {text}"
    _emitter.log_received.emit(level, formatted)


# Register the Qt sink with loguru
logger.add(_qt_log_sink, level="DEBUG", format="{message}")


class DevConsole(QDialog):
    """Developer console window — live log viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠  Jarvis Developer Console")
        self.setMinimumSize(900, 500)
        self.resize(1000, 600)
        self.setObjectName("devConsoleDialog")

        self._buffer: deque[tuple[str, str]] = deque(maxlen=2000)
        self._paused = False
        self._filter_text = ""
        self._min_level = "DEBUG"

        self._build_ui()
        _emitter.log_received.connect(self._on_log)

    # ── UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Toolbar ──────────────────────────────────────────────────
        toolbar = QHBoxLayout()

        title = QLabel("DEVELOPER CONSOLE")
        title.setObjectName("sectionHeader")
        toolbar.addWidget(title)
        toolbar.addStretch()

        # Level filter
        toolbar.addWidget(QLabel("Level:"))
        self._level_combo = QComboBox()
        self._level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_combo.setCurrentText("DEBUG")
        self._level_combo.currentTextChanged.connect(self._set_level)
        toolbar.addWidget(self._level_combo)

        # Text filter
        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter logs...")
        self._filter_input.setFixedWidth(200)
        self._filter_input.textChanged.connect(self._set_filter)
        toolbar.addWidget(self._filter_input)

        # Pause
        self._pause_btn = QPushButton("⏸ Pause")
        self._pause_btn.setCheckable(True)
        self._pause_btn.toggled.connect(self._toggle_pause)
        toolbar.addWidget(self._pause_btn)

        # Clear
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)

        # Auto-scroll
        self._autoscroll = QCheckBox("Auto-scroll")
        self._autoscroll.setChecked(True)
        toolbar.addWidget(self._autoscroll)

        layout.addLayout(toolbar)

        # ── Log display ───────────────────────────────────────────────
        self._console = QPlainTextEdit()
        self._console.setObjectName("devConsole")
        self._console.setReadOnly(True)
        mono_font = QFont("Cascadia Code", 9)
        if not mono_font.exactMatch():
            mono_font = QFont("Consolas", 9)
        self._console.setFont(mono_font)
        layout.addWidget(self._console)

        # ── Status bar ────────────────────────────────────────────────
        self._status = QLabel("Ready — 0 lines")
        self._status.setObjectName("statusLabel")
        layout.addWidget(self._status)

    # ── Log handling ──────────────────────────────────────────────────
    LEVEL_COLORS = {
        "DEBUG":    "#888888",
        "INFO":     "#00D4FF",
        "SUCCESS":  "#00FF88",
        "WARNING":  "#FFC400",
        "ERROR":    "#FF453A",
        "CRITICAL": "#FF2D55",
    }
    LEVEL_ORDER = ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

    def _on_log(self, level: str, text: str):
        self._buffer.append((level, text))
        if not self._paused:
            self._append_to_console(level, text)

    def _append_to_console(self, level: str, text: str):
        if not self._passes_filter(level, text):
            return

        color = self.LEVEL_COLORS.get(level, "#E8EAED")
        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")

        if self._autoscroll.isChecked():
            self._console.setTextCursor(cursor)
            self._console.ensureCursorVisible()

        self._status.setText(f"Lines: {self._console.document().blockCount()}")

    def _passes_filter(self, level: str, text: str) -> bool:
        # Level filter
        min_idx = self.LEVEL_ORDER.index(self._min_level) \
            if self._min_level in self.LEVEL_ORDER else 0
        cur_idx = self.LEVEL_ORDER.index(level) \
            if level in self.LEVEL_ORDER else 0
        if cur_idx < min_idx:
            return False
        # Text filter
        if self._filter_text and self._filter_text.lower() not in text.lower():
            return False
        return True

    def _toggle_pause(self, paused: bool):
        self._paused = paused
        self._pause_btn.setText("▶ Resume" if paused else "⏸ Pause")
        if not paused:
            # Flush buffer
            self._console.clear()
            for level, text in self._buffer:
                self._append_to_console(level, text)

    def _clear(self):
        self._console.clear()
        self._buffer.clear()

    def _set_level(self, level: str):
        self._min_level = level
        self._refresh()

    def _set_filter(self, text: str):
        self._filter_text = text
        self._refresh()

    def _refresh(self):
        self._console.clear()
        for level, text in self._buffer:
            self._append_to_console(level, text)
