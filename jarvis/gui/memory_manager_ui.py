"""
Memory Manager UI
==================
Browse, search, and manage long-term memories.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QTextEdit, QSplitter, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor

from jarvis.utils.logger import logger


class MemoryManagerUI(QWidget):
    """UI for browsing and managing the long-term memory store."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memories: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("MEMORY MANAGER")
        title.setObjectName("sectionHeader")
        header.addWidget(title)
        header.addStretch()
        self._count_label = QLabel("0 memories")
        self._count_label.setObjectName("statusLabel")
        header.addWidget(self._count_label)
        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(28)
        refresh_btn.clicked.connect(self.load_memories)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Search + filter
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Search memories...")
        self._search_input.textChanged.connect(self._apply_filter)
        search_row.addWidget(self._search_input)

        self._type_filter = QComboBox()
        self._type_filter.addItems(["All Types", "conversation", "preference",
                                    "note", "fact", "command"])
        self._type_filter.currentTextChanged.connect(self._apply_filter)
        self._type_filter.setFixedWidth(140)
        search_row.addWidget(self._type_filter)
        layout.addLayout(search_row)

        # Splitter: list + detail
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Memory list
        self._list = QListWidget()
        self._list.setMinimumWidth(280)
        self._list.currentRowChanged.connect(self._show_detail)
        splitter.addWidget(self._list)

        # Detail panel
        detail_frame = QFrame()
        detail_frame.setObjectName("glassPanel")
        detail_layout = QVBoxLayout(detail_frame)

        self._detail_title = QLabel("Select a memory to view details")
        self._detail_title.setStyleSheet("font-weight: 700; color: #00D4FF;")
        detail_layout.addWidget(self._detail_title)

        self._detail_type = QLabel("")
        self._detail_type.setObjectName("statusLabel")
        detail_layout.addWidget(self._detail_type)

        self._detail_content = QTextEdit()
        self._detail_content.setReadOnly(True)
        self._detail_content.setPlaceholderText("Memory content will appear here...")
        detail_layout.addWidget(self._detail_content)

        self._detail_meta = QLabel("")
        self._detail_meta.setObjectName("statusLabel")
        self._detail_meta.setWordWrap(True)
        detail_layout.addWidget(self._detail_meta)

        del_btn = QPushButton("🗑  Delete This Memory")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_selected)
        detail_layout.addWidget(del_btn)
        splitter.addWidget(detail_frame)

        splitter.setSizes([300, 500])
        layout.addWidget(splitter)

    def load_memories(self):
        """Load memories from the memory manager."""
        try:
            from jarvis.memory.memory_manager import memory_manager
            self._memories = memory_manager.get_all()
            self._apply_filter()
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            # Show placeholder data if memory not yet initialized
            self._memories = []
            self._list.clear()
            self._count_label.setText("Memory system not initialized")

    def _apply_filter(self):
        query = self._search_input.text().lower()
        type_filter = self._type_filter.currentText()

        self._list.clear()
        shown = 0
        for mem in self._memories:
            content = mem.get("content", "").lower()
            mtype = mem.get("type", "")
            if query and query not in content and query not in mtype:
                continue
            if type_filter != "All Types" and mtype != type_filter:
                continue

            item = QListWidgetItem()
            preview = mem.get("content", "")[:60].replace("\n", " ")
            item.setText(f"[{mtype}] {preview}")
            item.setData(Qt.ItemDataRole.UserRole, mem)
            if mtype == "conversation":
                item.setForeground(QColor("#00D4FF"))
            elif mtype == "preference":
                item.setForeground(QColor("#FFC400"))
            elif mtype == "note":
                item.setForeground(QColor("#00FF88"))
            self._list.addItem(item)
            shown += 1

        self._count_label.setText(f"{shown} of {len(self._memories)} memories")

    def _show_detail(self, row: int):
        item = self._list.item(row)
        if not item:
            return
        mem = item.data(Qt.ItemDataRole.UserRole)
        if not mem:
            return

        self._detail_title.setText(
            mem.get("content", "")[:80] + ("..." if len(mem.get("content", "")) > 80 else "")
        )
        self._detail_type.setText(f"Type: {mem.get('type', 'unknown')}")
        self._detail_content.setPlainText(mem.get("content", ""))
        self._detail_meta.setText(
            f"Created: {mem.get('created_at', 'unknown')} | "
            f"Importance: {mem.get('importance', 1)}"
        )

    def _delete_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        mem = item.data(Qt.ItemDataRole.UserRole)
        if not mem:
            return

        reply = QMessageBox.question(
            self, "Delete Memory",
            "Delete this memory permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from jarvis.memory.memory_manager import memory_manager
                memory_manager.delete(mem.get("id", ""))
                self.load_memories()
            except Exception as e:
                logger.error(f"Failed to delete memory: {e}")
