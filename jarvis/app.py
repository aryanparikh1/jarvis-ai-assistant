"""
Jarvis — QApplication Bootstrap
Handles app initialization, theming, and window management.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QFontDatabase

from jarvis.utils.config import config
from jarvis.utils.logger import logger
from jarvis.gui.main_window import MainWindow
from jarvis.gui.system_tray import JarvisTray


class JarvisApplication(QApplication):
    def __init__(self, argv: list):
        super().__init__(argv)

        # ── App metadata ────────────────────────────────────────────
        self.setApplicationName("Jarvis")
        self.setApplicationDisplayName("Jarvis AI Assistant")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("AryanParikh")
        self.setOrganizationDomain("jarvis.local")

        # ── High-DPI scaling ────────────────────────────────────────
        self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # ── Load stylesheet ─────────────────────────────────────────
        self._load_stylesheet()

        # ── Load fonts ──────────────────────────────────────────────
        self._load_fonts()

        # ── Create windows ──────────────────────────────────────────
        self.main_window = MainWindow()

        # ── System tray ─────────────────────────────────────────────
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = JarvisTray(self.main_window, self)
            self.tray.show()

        # ── Don't quit when last window closes (runs in tray) ───────
        self.setQuitOnLastWindowClosed(False)

        # ── Show main window ────────────────────────────────────────
        if not config.get("start_minimized", False):
            self.main_window.show()

        logger.info("Jarvis application started successfully")

    def _load_stylesheet(self):
        """Load the dark glassmorphism stylesheet."""
        qss_path = os.path.join(
            os.path.dirname(__file__), "gui", "styles", "dark_theme.qss"
        )
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            logger.warning(f"Stylesheet not found: {qss_path}")

    def _load_fonts(self):
        """Load custom fonts."""
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
        if os.path.isdir(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith((".ttf", ".otf")):
                    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, font_file))

        # Set default application font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
