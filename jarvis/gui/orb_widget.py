"""
Animated AI Orb Widget
========================
The iconic pulsing, glowing orb that shows Jarvis's state:
  - IDLE      → slow blue glow
  - LISTENING → pulsing teal ring
  - THINKING  → spinning gradient arc
  - SPEAKING  → oscillating waveform ring
"""

import math
from enum import Enum

from PySide6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QPropertyAnimation,
    QEasingCurve, Property, Signal
)
from PySide6.QtGui import (
    QPainter, QColor, QRadialGradient, QConicalGradient,
    QPen, QBrush, QLinearGradient, QPainterPath
)
from PySide6.QtWidgets import QWidget


class OrbState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


class OrbWidget(QWidget):
    """Animated AI orb that visualizes Jarvis state."""

    state_changed = Signal(str)

    # Color palettes per state
    PALETTES = {
        OrbState.IDLE: {
            "core": QColor(0, 180, 220),
            "glow": QColor(0, 120, 180),
            "ring": QColor(0, 212, 255),
        },
        OrbState.LISTENING: {
            "core": QColor(0, 230, 200),
            "glow": QColor(0, 180, 160),
            "ring": QColor(0, 255, 220),
        },
        OrbState.THINKING: {
            "core": QColor(140, 0, 255),
            "glow": QColor(100, 0, 200),
            "ring": QColor(180, 80, 255),
        },
        OrbState.SPEAKING: {
            "core": QColor(0, 200, 100),
            "glow": QColor(0, 150, 80),
            "ring": QColor(0, 255, 130),
        },
        OrbState.ERROR: {
            "core": QColor(255, 60, 60),
            "glow": QColor(200, 30, 30),
            "ring": QColor(255, 100, 100),
        },
    }

    def __init__(self, parent=None, size: int = 120):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._state = OrbState.IDLE
        self._angle = 0.0        # For spinning arc
        self._pulse = 0.0        # 0..1 pulse value
        self._wave_phase = 0.0   # For speaking wave
        self._glow_scale = 1.0   # Glow ring scale

        # ── Animation timer ──────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── State management ─────────────────────────────────────────────
    def set_state(self, state: OrbState):
        if self._state == state:
            return
        self._state = state
        self.state_changed.emit(state.value)

    @property
    def state(self) -> OrbState:
        return self._state

    # ── Tick ─────────────────────────────────────────────────────────
    def _tick(self):
        dt = 0.016  # ~16ms
        self._angle = (self._angle + 120 * dt) % 360      # 120°/s spin
        self._pulse = (self._pulse + dt * 1.5) % (2 * math.pi)
        self._wave_phase = (self._wave_phase + dt * 6) % (2 * math.pi)
        self.update()

    # ── Painting ──────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        palette = self.PALETTES[self._state]
        cx = self._size / 2
        cy = self._size / 2
        r = self._size / 2

        # ── 1. Outer glow ────────────────────────────────────────────
        glow_r = r * 0.85
        pulse_factor = 0.92 + 0.08 * math.sin(self._pulse)
        self._draw_glow(painter, cx, cy, glow_r * pulse_factor, palette["glow"])

        # ── 2. State-specific ring ───────────────────────────────────
        if self._state == OrbState.IDLE:
            self._draw_idle_ring(painter, cx, cy, r * 0.75, palette)
        elif self._state == OrbState.LISTENING:
            self._draw_listening_ring(painter, cx, cy, r * 0.75, palette)
        elif self._state == OrbState.THINKING:
            self._draw_thinking_arc(painter, cx, cy, r * 0.75, palette)
        elif self._state == OrbState.SPEAKING:
            self._draw_speaking_wave(painter, cx, cy, r * 0.75, palette)
        elif self._state == OrbState.ERROR:
            self._draw_idle_ring(painter, cx, cy, r * 0.75, palette)

        # ── 3. Core orb ──────────────────────────────────────────────
        self._draw_core(painter, cx, cy, r * 0.45, palette["core"])

        # ── 4. Highlight (lens flare) ────────────────────────────────
        self._draw_highlight(painter, cx, cy, r * 0.3)

        painter.end()

    def _draw_glow(self, painter, cx, cy, radius, color):
        grad = QRadialGradient(QPointF(cx, cy), radius)
        c = QColor(color)
        c.setAlpha(60)
        grad.setColorAt(0, c)
        c2 = QColor(color)
        c2.setAlpha(0)
        grad.setColorAt(1, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_core(self, painter, cx, cy, radius, color):
        grad = QRadialGradient(QPointF(cx - radius * 0.3, cy - radius * 0.3), radius)
        light = color.lighter(150)
        light.setAlpha(255)
        grad.setColorAt(0, light)
        dark = color.darker(130)
        dark.setAlpha(230)
        grad.setColorAt(1, dark)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_highlight(self, painter, cx, cy, radius):
        grad = QRadialGradient(QPointF(cx - radius * 0.2, cy - radius * 0.3), radius)
        grad.setColorAt(0, QColor(255, 255, 255, 80))
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(
            QPointF(cx - radius * 0.15, cy - radius * 0.2),
            radius * 0.5, radius * 0.4
        )

    def _draw_idle_ring(self, painter, cx, cy, radius, palette):
        pulse = 0.5 + 0.5 * math.sin(self._pulse)
        color = QColor(palette["ring"])
        color.setAlpha(int(60 + 60 * pulse))
        pen = QPen(color, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_listening_ring(self, painter, cx, cy, radius, palette):
        """Concentric pulsing rings."""
        for i in range(3):
            phase = self._pulse + i * (2 * math.pi / 3)
            scale = 1.0 + 0.25 * i
            alpha = int(120 * (1 - i * 0.3) * (0.5 + 0.5 * math.sin(phase)))
            color = QColor(palette["ring"])
            color.setAlpha(max(0, alpha))
            pen = QPen(color, max(0.5, 2.0 - i * 0.5))
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius * scale, radius * scale)

    def _draw_thinking_arc(self, painter, cx, cy, radius, palette):
        """Spinning gradient arc."""
        pen = QPen(palette["ring"], 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        start_angle = int(self._angle * 16)
        span = 250 * 16  # 250° arc
        painter.drawArc(rect, start_angle, span)

        # Second arc offset
        pen2 = QPen(palette["core"], 1.5)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.drawArc(rect, start_angle + 130 * 16, 80 * 16)

    def _draw_speaking_wave(self, painter, cx, cy, radius, palette):
        """Oscillating wave ring."""
        path = QPainterPath()
        steps = 72
        for i in range(steps + 1):
            angle_rad = (i / steps) * 2 * math.pi
            wave = 1.0 + 0.12 * math.sin(angle_rad * 6 + self._wave_phase)
            r = radius * wave
            x = cx + r * math.cos(angle_rad)
            y = cy + r * math.sin(angle_rad)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()

        color = QColor(palette["ring"])
        color.setAlpha(180)
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
