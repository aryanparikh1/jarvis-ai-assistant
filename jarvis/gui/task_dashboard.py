"""
Task Dashboard
===============
Displays scheduled tasks, reminders, and workflow status.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QDateTimeEdit, QDialogButtonBox,
    QFrame
)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QColor

from jarvis.utils.logger import logger


class AddTaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Task")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Task name...")
        form.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["reminder", "scheduled", "recurring"])
        form.addRow("Type:", self.type_combo)

        self.trigger_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.trigger_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        form.addRow("Trigger At:", self.trigger_dt)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Action or command...")
        form.addRow("Action:", self.command_input)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_task(self) -> dict:
        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "trigger": self.trigger_dt.dateTime().toPython(),
            "command": self.command_input.text(),
            "status": "pending",
        }


class TaskDashboard(QWidget):
    """Task and scheduler dashboard."""

    task_added = Signal(dict)
    task_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("TASK DASHBOARD")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel("0 tasks")
        self._count_label.setObjectName("statusLabel")
        header.addWidget(self._count_label)

        add_btn = QPushButton("＋  Add Task")
        add_btn.setFixedHeight(32)
        add_btn.clicked.connect(self._add_task)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Stats row
        stats = QHBoxLayout()
        for label, color, attr in [
            ("Pending", "#FFC400", "_pending_count"),
            ("Running", "#00D4FF", "_running_count"),
            ("Completed", "#00FF88", "_done_count"),
            ("Failed", "#FF453A", "_fail_count"),
        ]:
            card = QFrame()
            card.setObjectName("glassPanel")
            card.setFixedHeight(60)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            count = QLabel("0")
            count.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {color};")
            count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl = QLabel(label)
            name_lbl.setObjectName("statusLabel")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(count)
            card_layout.addWidget(name_lbl)
            setattr(self, attr, count)
            stats.addWidget(card)
        layout.addLayout(stats)

        # Task table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Type", "Trigger", "Action", "Status"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self._table)

        # Delete button
        del_btn = QPushButton("🗑  Delete Selected")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_selected)
        layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task = dialog.get_task()
            self._tasks.append(task)
            self._refresh_table()
            self.task_added.emit(task)

    def _delete_selected(self):
        rows = set(idx.row() for idx in self._table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            if row < len(self._tasks):
                t = self._tasks.pop(row)
                self.task_deleted.emit(t.get("name", ""))
        self._refresh_table()

    def add_task_programmatic(self, task: dict):
        self._tasks.append(task)
        self._refresh_table()

    def update_task_status(self, name: str, status: str):
        for t in self._tasks:
            if t.get("name") == name:
                t["status"] = status
        self._refresh_table()

    def _refresh_table(self):
        self._table.setRowCount(len(self._tasks))
        pending = running = done = failed = 0
        for i, task in enumerate(self._tasks):
            status = task.get("status", "pending")
            items = [
                task.get("name", ""),
                task.get("type", ""),
                str(task.get("trigger", ""))[:16],
                task.get("command", ""),
                status,
            ]
            for j, text in enumerate(items):
                item = QTableWidgetItem(text)
                if j == 4:  # Status column color
                    color = {
                        "pending": "#FFC400",
                        "running": "#00D4FF",
                        "completed": "#00FF88",
                        "failed": "#FF453A",
                    }.get(status, "#888")
                    item.setForeground(QColor(color))
                self._table.setItem(i, j, item)
            if status == "pending":
                pending += 1
            elif status == "running":
                running += 1
            elif status == "completed":
                done += 1
            elif status == "failed":
                failed += 1

        self._pending_count.setText(str(pending))
        self._running_count.setText(str(running))
        self._done_count.setText(str(done))
        self._fail_count.setText(str(failed))
        self._count_label.setText(f"{len(self._tasks)} task{'s' if len(self._tasks) != 1 else ''}")
