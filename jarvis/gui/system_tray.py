"""
System Tray Integration
========================
System tray icon with context menu for quick actions.
"""

import os
from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QSize

from jarvis.utils.logger import logger


def _create_fallback_icon(size: int = 32) -> QIcon:
    """Create a simple J icon if no icon file is found."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor(0, 212, 255)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPixelSize(int(size * 0.55))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "J")
    painter.end()
    return QIcon(pixmap)


class JarvisTray(QSystemTrayIcon):
    def __init__(self, main_window, app: QApplication):
        self._main_window = main_window
        self._app = app

        # ── Load icon ────────────────────────────────────────────────
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "assets", "icons", "jarvis.ico"
        )
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = _create_fallback_icon()

        super().__init__(icon, app)
        self.setToolTip("Jarvis AI Assistant")

        # ── Context menu ─────────────────────────────────────────────
        self._menu = QMenu()
        self._build_menu()
        self.setContextMenu(self._menu)

        # ── Click behavior ───────────────────────────────────────────
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        self._menu.clear()

        # Header (non-clickable)
        header = self._menu.addAction("⚡ Jarvis AI Assistant")
        header.setEnabled(False)
        self._menu.addSeparator()

        # Actions
        show_action = self._menu.addAction("🖥  Show / Hide")
        show_action.triggered.connect(self._toggle_window)

        new_chat_action = self._menu.addAction("💬  New Chat")
        new_chat_action.triggered.connect(self._new_chat)

        settings_action = self._menu.addAction("⚙  Settings")
        settings_action.triggered.connect(self._open_settings)

        self._menu.addSeparator()

        voice_action = self._menu.addAction("🎤  Enable Voice")
        voice_action.setCheckable(True)
        voice_action.setChecked(True)
        self._voice_action = voice_action

        self._menu.addSeparator()

        quit_action = self._menu.addAction("✕  Quit Jarvis")
        quit_action.triggered.connect(self._quit)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _toggle_window(self):
        if self._main_window.isVisible():
            self._main_window.hide()
        else:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()

    def _new_chat(self):
        self._main_window.show()
        self._main_window.raise_()
        if hasattr(self._main_window, "new_chat"):
            self._main_window.new_chat()

    def _open_settings(self):
        self._main_window.show()
        if hasattr(self._main_window, "open_settings"):
            self._main_window.open_settings()

    def _quit(self):
        logger.info("Jarvis quit requested from tray")
        self._app.quit()

    def notify(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information):
        """Show a system tray notification bubble."""
        self.showMessage(title, message, icon, 4000)
