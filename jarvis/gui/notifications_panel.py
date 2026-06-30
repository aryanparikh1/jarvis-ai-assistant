"""
Notifications Panel
====================
In-app notification center that shows alerts, reminders, and system messages.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea,
    QWidget, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from jarvis.gui.styles.animations import fade_in


class NotificationItem(QFrame):
    """A single notification card."""

    dismissed = Signal(object)

    def __init__(self, title: str, body: str, priority: str = "normal",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("notificationItem")
        self.setProperty("priority", priority)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-weight: 700; font-size: 9pt; color: "
            f"{'#FF453A' if priority == 'high' else '#FFC400' if priority == 'medium' else '#00D4FF'};"
        )
        header.addWidget(title_label)
        header.addStretch()

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setObjectName("statusLabel")
        header.addWidget(time_label)

        dismiss_btn = QPushButton("×")
        dismiss_btn.setFixedSize(20, 20)
        dismiss_btn.setStyleSheet(
            "QPushButton { background: transparent; color: rgba(255,255,255,0.4); "
            "font-size: 14pt; border: none; padding: 0; }"
            "QPushButton:hover { color: #FF453A; }"
        )
        dismiss_btn.clicked.connect(lambda: self.dismissed.emit(self))
        header.addWidget(dismiss_btn)

        layout.addLayout(header)

        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 9pt;")
        layout.addWidget(body_label)

        self.style().polish(self)


class NotificationsPanel(QDialog):
    """Notification center — shows and manages in-app notifications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔔  Notifications")
        self.setMinimumWidth(420)
        self.setMaximumWidth(500)
        self.resize(450, 600)
        self._notifications: list[NotificationItem] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("NOTIFICATIONS")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel("0 items")
        self._count_label.setObjectName("statusLabel")
        header.addWidget(self._count_label)

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self.clear_all)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_widget = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_widget)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(8)
        self._scroll_layout.addStretch()
        self._scroll.setWidget(self._scroll_widget)
        layout.addWidget(self._scroll)

        # Empty state
        self._empty_label = QLabel("✓  All caught up!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 12pt; padding: 40px;")
        layout.addWidget(self._empty_label)

    def add_notification(
        self, title: str, body: str, priority: str = "normal",
        auto_dismiss: int = 0
    ):
        """Add a notification. priority: 'normal' | 'medium' | 'high'."""
        item = NotificationItem(title, body, priority)
        item.dismissed.connect(self._remove_item)
        self._notifications.append(item)

        # Insert before the stretch
        idx = self._scroll_layout.count() - 1
        self._scroll_layout.insertWidget(idx, item)

        anim = fade_in(item, 250)
        anim.start()

        self._update_ui()

        if auto_dismiss > 0:
            QTimer.singleShot(auto_dismiss, lambda: self._remove_item(item))

    def _remove_item(self, item: NotificationItem):
        if item in self._notifications:
            self._notifications.remove(item)
            item.setParent(None)
            item.deleteLater()
            self._update_ui()

    def clear_all(self):
        for item in list(self._notifications):
            item.setParent(None)
            item.deleteLater()
        self._notifications.clear()
        self._update_ui()

    def _update_ui(self):
        count = len(self._notifications)
        self._count_label.setText(f"{count} item{'s' if count != 1 else ''}")
        self._empty_label.setVisible(count == 0)
        self._scroll.setVisible(count > 0)

    @property
    def unread_count(self) -> int:
        return len(self._notifications)
