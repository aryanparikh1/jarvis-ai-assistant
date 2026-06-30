"""
Animated Microphone Indicator
==============================
Displays mic state with animated rings and audio level bar.
States: OFF, PUSH_TO_TALK, ACTIVE, VAD_SPEECH
"""

import math
from enum import Enum

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, QPainterPath
)
from PySide6.QtWidgets import QWidget


class MicState(Enum):
    OFF = "off"
    STANDBY = "standby"
    ACTIVE = "active"
    SPEECH = "speech"


class MicIndicator(QWidget):
    """Compact animated microphone indicator widget."""

    clicked = Signal()

    def __init__(self, parent=None, size: int = 48):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._state = MicState.OFF
        self._phase = 0.0
        self._audio_level = 0.0  # 0..1, set externally

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_state(self, state: MicState):
        self._state = state
        self.update()

    def set_audio_level(self, level: float):
        """Set audio level (0.0 to 1.0) for visualisation."""
        self._audio_level = max(0.0, min(1.0, level))

    def _tick(self):
        self._phase = (self._phase + 0.05) % (2 * math.pi)
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self._size / 2
        cy = self._size / 2
        r = self._size / 2 - 4

        # ── Background circle ────────────────────────────────────────
        if self._state == MicState.OFF:
            bg = QColor(40, 40, 60, 180)
        elif self._state == MicState.STANDBY:
            bg = QColor(0, 80, 100, 180)
        elif self._state == MicState.ACTIVE:
            bg = QColor(0, 120, 140, 200)
        else:  # SPEECH
            bg = QColor(0, 180, 100, 200)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # ── Pulse ring ───────────────────────────────────────────────
        if self._state in (MicState.ACTIVE, MicState.SPEECH):
            pulse = 0.5 + 0.5 * math.sin(self._phase)
            ring_r = r + 4 + 3 * pulse
            ring_alpha = int(150 * (1 - pulse * 0.5))
            ring_color = QColor(0, 255, 180, ring_alpha) \
                if self._state == MicState.SPEECH else QColor(0, 212, 255, ring_alpha)
            pen = QPen(ring_color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # ── Mic icon ─────────────────────────────────────────────────
        icon_color = QColor(255, 255, 255, 220) \
            if self._state != MicState.OFF else QColor(150, 150, 150, 180)
        self._draw_mic_icon(painter, cx, cy, r * 0.55, icon_color)

        painter.end()

    def _draw_mic_icon(self, painter, cx, cy, scale, color):
        """Draw a simple mic shape."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))

        # Mic body (rounded rect)
        body_w = scale * 0.4
        body_h = scale * 0.7
        body_r = body_w / 2
        painter.drawRoundedRect(
            QRectF(cx - body_w / 2, cy - body_h * 0.65,
                   body_w, body_h),
            body_r, body_r
        )

        # Stand arc
        pen = QPen(color, scale * 0.1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_r = scale * 0.45
        painter.drawArc(
            QRectF(cx - arc_r, cy - arc_r * 0.4, arc_r * 2, arc_r),
            0, -180 * 16
        )
        # Stand stem
        painter.drawLine(
            QPointF(cx, cy + arc_r * 0.55),
            QPointF(cx, cy + scale * 0.7)
        )
        # Stand base
        base_w = scale * 0.5
        painter.drawLine(
            QPointF(cx - base_w / 2, cy + scale * 0.7),
            QPointF(cx + base_w / 2, cy + scale * 0.7)
        )
