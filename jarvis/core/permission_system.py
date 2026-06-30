"""
Permission System
==================
Gate-keeps all Jarvis actions by risk level.

Risk Levels:
  SAFE     (0) → auto-execute, no confirmation needed
  MEDIUM   (1) → ask once per session
  DANGEROUS(2) → always confirm before executing
"""

import threading
from enum import IntEnum
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QApplication

from jarvis.utils.logger import logger


class Risk(IntEnum):
    SAFE = 0
    MEDIUM = 1
    DANGEROUS = 2


# ── Pre-defined action risk table ──────────────────────────────────────────
ACTION_RISKS: dict[str, Risk] = {
    # Safe
    "search_web": Risk.SAFE,
    "read_clipboard": Risk.SAFE,
    "get_time": Risk.SAFE,
    "open_app": Risk.SAFE,
    "media_control": Risk.SAFE,
    "get_volume": Risk.SAFE,
    "set_volume": Risk.SAFE,
    "get_brightness": Risk.SAFE,
    "read_file": Risk.SAFE,
    "list_directory": Risk.SAFE,
    "web_summarize": Risk.SAFE,
    "get_weather": Risk.SAFE,
    "screenshot": Risk.SAFE,
    # Medium
    "write_clipboard": Risk.MEDIUM,
    "write_file": Risk.MEDIUM,
    "create_file": Risk.MEDIUM,
    "send_notification": Risk.MEDIUM,
    "fill_form": Risk.MEDIUM,
    "browser_navigate": Risk.MEDIUM,
    "browser_click": Risk.MEDIUM,
    "schedule_task": Risk.MEDIUM,
    "create_reminder": Risk.MEDIUM,
    "set_brightness": Risk.MEDIUM,
    "move_file": Risk.MEDIUM,
    "rename_file": Risk.MEDIUM,
    # Dangerous
    "delete_file": Risk.DANGEROUS,
    "delete_folder": Risk.DANGEROUS,
    "run_terminal_command": Risk.DANGEROUS,
    "close_app": Risk.DANGEROUS,
    "kill_process": Risk.DANGEROUS,
    "modify_registry": Risk.DANGEROUS,
    "install_software": Risk.DANGEROUS,
    "format_disk": Risk.DANGEROUS,
    "send_email": Risk.DANGEROUS,
    "purchase": Risk.DANGEROUS,
}


class PermissionSystem(QObject):
    """Manages action permissions with session-based 'ask once' logic."""

    permission_requested = Signal(str, str, int)  # action, description, risk

    def __init__(self):
        super().__init__()
        self._session_granted: set[str] = set()  # medium-risk actions approved this session
        self._lock = threading.Lock()

    def get_risk(self, action: str) -> Risk:
        return ACTION_RISKS.get(action, Risk.MEDIUM)

    def can_execute(self, action: str, description: str = "") -> bool:
        """
        Check if an action is allowed. Shows confirmation dialog if needed.
        Returns True if the action should proceed, False if blocked.
        """
        risk = self.get_risk(action)

        if risk == Risk.SAFE:
            logger.debug(f"[SAFE] Auto-executing: {action}")
            return True

        if risk == Risk.MEDIUM:
            with self._lock:
                if action in self._session_granted:
                    logger.debug(f"[MEDIUM] Session-granted: {action}")
                    return True
            # Ask user
            granted = self._show_dialog(action, description, risk)
            if granted:
                with self._lock:
                    self._session_granted.add(action)
            return granted

        if risk == Risk.DANGEROUS:
            return self._show_dialog(action, description, risk)

        return False

    def _show_dialog(self, action: str, description: str, risk: Risk) -> bool:
        """Show a confirmation dialog (must run on main thread)."""
        icon = (
            QMessageBox.Icon.Warning if risk == Risk.MEDIUM
            else QMessageBox.Icon.Critical
        )
        title = (
            "⚠️ Permission Required" if risk == Risk.MEDIUM
            else "🚨 Dangerous Action — Confirm"
        )
        msg_text = description or f"Jarvis wants to perform: {action}"
        detail = {
            Risk.MEDIUM: "This is a medium-risk action. Approving will allow it for the rest of this session.",
            Risk.DANGEROUS: "⛔ This is a DANGEROUS action and cannot be undone. Only proceed if you're sure.",
        }.get(risk, "")

        box = QMessageBox()
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(msg_text)
        box.setDetailedText(detail)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)

        result = box.exec()
        granted = result == QMessageBox.StandardButton.Yes
        logger.info(
            f"Permission {'granted' if granted else 'denied'} for [{risk.name}] {action}"
        )
        return granted

    def grant(self, action: str):
        """Programmatically grant a medium-risk action for this session."""
        with self._lock:
            self._session_granted.add(action)

    def revoke(self, action: str):
        with self._lock:
            self._session_granted.discard(action)

    def clear_session(self):
        with self._lock:
            self._session_granted.clear()


# Singleton
permissions = PermissionSystem()
