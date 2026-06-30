"""
Qt Animation Helpers
====================
Reusable animation factories for glassmorphism UI effects.
"""

from PySide6.QtCore import (
    QPropertyAnimation, QSequentialAnimationGroup,
    QParallelAnimationGroup, QEasingCurve, QRect, QPoint, QSize,
    Qt, QAbstractAnimation
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect


def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """Fade a widget in from transparent to opaque."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


def fade_out(widget: QWidget, duration: int = 300,
             hide_on_finish: bool = True) -> QPropertyAnimation:
    """Fade a widget out."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)
    if hide_on_finish:
        anim.finished.connect(widget.hide)
    return anim


def slide_in_from_bottom(widget: QWidget, duration: int = 350) -> QPropertyAnimation:
    """Slide a widget in from below."""
    geo = widget.geometry()
    start = QRect(geo.x(), geo.y() + 40, geo.width(), geo.height())
    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(geo)
    anim.setEasingCurve(QEasingCurve.Type.OutBack)
    return anim


def slide_in_from_right(widget: QWidget, duration: int = 350) -> QPropertyAnimation:
    """Slide a widget in from the right."""
    geo = widget.geometry()
    start = QRect(geo.x() + 60, geo.y(), geo.width(), geo.height())
    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(geo)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    return anim


def pulse(widget: QWidget, min_opacity: float = 0.4,
          max_opacity: float = 1.0, duration: int = 800) -> QSequentialAnimationGroup:
    """Continuously pulse a widget's opacity."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    fade_down = QPropertyAnimation(effect, b"opacity")
    fade_down.setDuration(duration)
    fade_down.setStartValue(max_opacity)
    fade_down.setEndValue(min_opacity)
    fade_down.setEasingCurve(QEasingCurve.Type.InOutSine)

    fade_up = QPropertyAnimation(effect, b"opacity")
    fade_up.setDuration(duration)
    fade_up.setStartValue(min_opacity)
    fade_up.setEndValue(max_opacity)
    fade_up.setEasingCurve(QEasingCurve.Type.InOutSine)

    group = QSequentialAnimationGroup(widget)
    group.addAnimation(fade_down)
    group.addAnimation(fade_up)
    group.setLoopCount(-1)  # Infinite
    return group


def bounce_in(widget: QWidget, duration: int = 500) -> QParallelAnimationGroup:
    """Fade in + scale-like bounce using geometry."""
    geo = widget.geometry()
    cx, cy = geo.center().x(), geo.center().y()
    shrunk = QRect(cx - geo.width() // 4, cy - geo.height() // 4,
                   geo.width() // 2, geo.height() // 2)

    geo_anim = QPropertyAnimation(widget, b"geometry")
    geo_anim.setDuration(duration)
    geo_anim.setStartValue(shrunk)
    geo_anim.setEndValue(geo)
    geo_anim.setEasingCurve(QEasingCurve.Type.OutElastic)

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    fade = QPropertyAnimation(effect, b"opacity")
    fade.setDuration(duration // 2)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(geo_anim)
    group.addAnimation(fade)
    return group
