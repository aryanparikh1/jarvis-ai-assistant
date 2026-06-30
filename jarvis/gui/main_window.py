"""
Main Window — Jarvis Chat Interface
=====================================
The primary application window featuring:
  - Sidebar navigation (Chat, Voice, Tasks, Memory, Settings)
  - Chat area with streaming markdown-style messages
  - Animated AI orb and mic indicator in header
  - Real-time LLM streaming responses
  - Keyboard shortcuts
  - Glassmorphism dark UI
"""

import asyncio
import re
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QTextEdit,
    QSizePolicy, QStackedWidget, QApplication,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QRunnable, QThreadPool, QObject
)
from PySide6.QtGui import (
    QColor, QKeySequence, QFont, QPixmap, QPainter, QLinearGradient,
    QTextCursor, QShortcut
)

from jarvis.gui.orb_widget import OrbWidget, OrbState
from jarvis.gui.mic_indicator import MicIndicator, MicState
from jarvis.gui.voice_panel import VoicePanel
from jarvis.gui.task_dashboard import TaskDashboard
from jarvis.gui.memory_manager_ui import MemoryManagerUI
from jarvis.gui.notifications_panel import NotificationsPanel
from jarvis.gui.dev_console import DevConsole
from jarvis.gui.settings_window import SettingsWindow
from jarvis.utils.config import config
from jarvis.utils.logger import logger


# ── Async bridge to run coroutines from Qt ────────────────────────────────────
class AsyncWorker(QObject):
    """Runs an async coroutine and emits chunks via signals."""
    chunk_received = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, coro):
        super().__init__()
        self._coro = coro

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._collect())
        finally:
            loop.close()

    async def _collect(self):
        full = ""
        try:
            async for chunk in self._coro:
                full += chunk
                self.chunk_received.emit(chunk)
            self.finished.emit(full)
        except Exception as e:
            self.error.emit(str(e))


class LLMThread(QThread):
    chunk_received = Signal(str)
    finished = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, user_message: str, parent=None):
        super().__init__(parent)
        self._user_message = user_message

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._stream())
        finally:
            loop.close()

    async def _stream(self):
        from jarvis.core.brain import brain
        full = ""
        try:
            async for chunk in brain.stream_response(self._user_message):
                full += chunk
                self.chunk_received.emit(chunk)
            self.finished.emit(full)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ── Message Bubble ────────────────────────────────────────────────────────────
class MessageBubble(QFrame):
    """Chat message bubble (user or assistant)."""

    def __init__(self, role: str, content: str = "", parent=None):
        super().__init__(parent)
        self._role = role
        self.setObjectName("userBubble" if role == "user" else "assistantBubble")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Header row ───────────────────────────────────────────────
        header = QHBoxLayout()
        icon_text = "You" if role == "user" else "⚡ Jarvis"
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(
            f"font-weight: 800; font-size: 9pt; color: "
            f"{'#00D4FF' if role != 'user' else '#A78BFA'};"
        )
        header.addWidget(icon_label)
        header.addStretch()
        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setObjectName("statusLabel")
        header.addWidget(time_label)
        layout.addLayout(header)

        # ── Content ──────────────────────────────────────────────────
        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content.setStyleSheet(
            "QTextEdit { background: transparent; border: none; padding: 0; "
            "color: #E8EAED; font-size: 10pt; }"
        )
        self._content.document().setDocumentMargin(0)
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        if content:
            self._set_content(content)
        layout.addWidget(self._content)
        self._update_height()

    def _set_content(self, text: str):
        # Simple markdown-ish rendering via HTML
        html = self._markdown_to_html(text)
        self._content.setHtml(html)
        self._update_height()

    def append_chunk(self, chunk: str):
        """Append a streaming chunk."""
        cursor = self._content.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self._content.setTextCursor(cursor)
        self._update_height()

    def set_full_content(self, text: str):
        """Replace content with fully formatted version."""
        html = self._markdown_to_html(text)
        self._content.setHtml(html)
        self._update_height()

    def _update_height(self):
        doc_height = int(self._content.document().size().height())
        self._content.setFixedHeight(max(24, doc_height + 8))

    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """Convert basic markdown to HTML for display."""
        # Code blocks
        text = re.sub(
            r'```(\w+)?\n(.*?)```',
            r'<pre style="background:#0A0E1A; border:1px solid rgba(0,212,255,0.2); '
            r'border-radius:8px; padding:12px; font-family:Consolas,monospace; '
            r'font-size:9pt; color:#00FF88;">\2</pre>',
            text, flags=re.DOTALL
        )
        # Inline code
        text = re.sub(
            r'`([^`]+)`',
            r'<code style="background:rgba(0,212,255,0.1); border-radius:3px; '
            r'padding:1px 5px; font-family:Consolas,monospace; color:#00D4FF;">\1</code>',
            text
        )
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # Headers
        text = re.sub(r'^### (.+)$', r'<h3 style="color:#00D4FF;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2 style="color:#00D4FF;">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1 style="color:#00D4FF;">\1</h1>', text, flags=re.MULTILINE)
        # Bullet points
        text = re.sub(r'^[•\-\*] (.+)$', r'• \1', text, flags=re.MULTILINE)
        # Newlines
        text = text.replace('\n', '<br>')
        return f'<span style="color:#E8EAED; font-size:10pt; line-height:1.6;">{text}</span>'


# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """The primary Jarvis application window."""

    def __init__(self):
        super().__init__()
        self._llm_thread: LLMThread | None = None
        self._current_assistant_bubble: MessageBubble | None = None
        self._full_response = ""
        self._chat_history_widget = None
        self._notifications = NotificationsPanel(self)
        self._dev_console = DevConsole(self)
        self._settings_window = SettingsWindow(self)

        self._setup_window()
        self._build_ui()
        self._setup_shortcuts()
        self._show_welcome()

        logger.info("Main window initialized")

    # ── Window setup ──────────────────────────────────────────────────
    def _setup_window(self):
        self.setWindowTitle("Jarvis AI Assistant")
        self.setMinimumSize(1000, 700)
        self.resize(1280, 800)

        # Window flags for frameless + translucency
        # Keep standard frame for now (better compatibility)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )

    # ── UI Construction ───────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────
        root.addWidget(self._build_sidebar())

        # ── Main area ─────────────────────────────────────────────────
        main_area = QVBoxLayout()
        main_area.setContentsMargins(0, 0, 0, 0)
        main_area.setSpacing(0)

        main_area.addWidget(self._build_header())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_chat_page())      # 0
        self._stack.addWidget(self._build_voice_page())     # 1
        self._stack.addWidget(self._build_tasks_page())     # 2
        self._stack.addWidget(self._build_memory_page())    # 3
        self._stack.addWidget(self._build_about_page())     # 4
        main_area.addWidget(self._stack)

        root.addLayout(main_area)

    # ── Sidebar ───────────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Logo
        logo_row = QHBoxLayout()
        logo_text = QLabel("⚡ JARVIS")
        logo_text.setStyleSheet(
            "font-size: 16pt; font-weight: 900; color: #00D4FF; letter-spacing: 4px;"
        )
        logo_row.addWidget(logo_text)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        version = QLabel("v1.0.0  •  AI Assistant")
        version.setObjectName("statusLabel")
        layout.addWidget(version)

        layout.addSpacing(20)

        # Nav buttons
        self._nav_buttons: list[QPushButton] = []
        nav_items = [
            ("💬", "Chat", 0),
            ("🎤", "Voice", 1),
            ("📅", "Tasks", 2),
            ("🧠", "Memory", 3),
            ("ℹ", "About", 4),
        ]
        for icon, name, idx in nav_items:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("sidebarBtn")
            btn.setFixedHeight(44)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom actions
        for icon, name, slot in [
            ("🔔", "Notifications", self._show_notifications),
            ("🛠", "Dev Console", self._show_dev_console),
            ("⚙", "Settings", self.open_settings),
        ]:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("sidebarBtn")
            btn.setFixedHeight(44)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        # Status indicator
        layout.addSpacing(12)
        self._status_dot = QLabel("● Connected")
        self._status_dot.setStyleSheet("color: #00FF88; font-size: 8pt;")
        layout.addWidget(self._status_dot)

        self._nav_buttons[0].setChecked(True)
        self._nav_buttons[0].setProperty("active", "true")
        return sidebar

    def _switch_page(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == idx)
            btn.setProperty("active", "true" if i == idx else "false")
            btn.style().polish(btn)

    # ── Header ────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("titleBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 8, 16, 8)
        layout.setSpacing(12)

        # Orb
        self.orb = OrbWidget(size=36)
        layout.addWidget(self.orb)

        # Title
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("JARVIS")
        title.setObjectName("titleLabel")
        title_col.addWidget(title)
        self._header_status = QLabel("AI Desktop Assistant  •  Ready")
        self._header_status.setObjectName("subtitleLabel")
        title_col.addWidget(self._header_status)
        layout.addLayout(title_col)

        layout.addStretch()

        # Mic indicator
        self.mic_indicator = MicIndicator(size=36)
        layout.addWidget(self.mic_indicator)

        # New chat button
        new_chat_btn = QPushButton("＋ New Chat")
        new_chat_btn.setFixedHeight(32)
        new_chat_btn.clicked.connect(self.new_chat)
        layout.addWidget(new_chat_btn)

        return header

    # ── Chat Page ─────────────────────────────────────────────────────
    def _build_chat_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Chat scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setObjectName("chatContainer")

        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(16, 16, 16, 16)
        self._chat_layout.setSpacing(16)
        self._chat_layout.addStretch()
        self._scroll.setWidget(self._chat_container)
        layout.addWidget(self._scroll, stretch=1)

        # Input area
        input_area = QHBoxLayout()
        input_area.setSpacing(10)

        self._chat_input = QTextEdit()
        self._chat_input.setObjectName("chatInput")
        self._chat_input.setPlaceholderText("Ask Jarvis anything... (Ctrl+Enter to send)")
        self._chat_input.setMaximumHeight(120)
        self._chat_input.setMinimumHeight(52)
        input_area.addWidget(self._chat_input)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("sendBtn")
        send_btn.setFixedSize(80, 52)
        send_btn.clicked.connect(self._send_message)
        input_area.addWidget(send_btn)

        layout.addLayout(input_area)

        # Suggestion chips
        chips_layout = QHBoxLayout()
        chips = [
            "What can you do?",
            "Open Chrome",
            "Search the web for...",
            "Set a reminder",
        ]
        for chip_text in chips:
            chip = QPushButton(chip_text)
            chip.setObjectName("chip")
            chip.setFixedHeight(28)
            chip.clicked.connect(lambda _, t=chip_text: self._quick_message(t))
            chips_layout.addWidget(chip)
        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        return page

    def _build_voice_page(self) -> QWidget:
        self._voice_panel = VoicePanel()
        self._voice_panel.voice_text_ready.connect(self._chat_input.setPlainText)
        return self._voice_panel

    def _build_tasks_page(self) -> QWidget:
        self._task_dashboard = TaskDashboard()
        return self._task_dashboard

    def _build_memory_page(self) -> QWidget:
        self._memory_ui = MemoryManagerUI()
        return self._memory_ui

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        orb = OrbWidget(size=120)
        layout.addWidget(orb, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)

        title = QLabel("JARVIS AI ASSISTANT")
        title.setStyleSheet(
            "font-size: 24pt; font-weight: 900; color: #00D4FF; letter-spacing: 6px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Version 1.0.0  •  Built by Aryan Parikh")
        sub.setObjectName("statusLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(24)
        desc = QLabel(
            "Jarvis is an advanced AI desktop assistant that combines the power of\n"
            "large language models with full computer control capabilities.\n\n"
            "Inspired by Iron Man's J.A.R.V.I.S. — Just A Rather Very Intelligent System."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11pt; line-height: 1.6;")
        layout.addWidget(desc)

        layout.addStretch()
        return page

    # ── Chat Logic ────────────────────────────────────────────────────
    def _send_message(self):
        text = self._chat_input.toPlainText().strip()
        if not text:
            return
        self._chat_input.clear()
        self._process_message(text)

    def _quick_message(self, text: str):
        self._process_message(text)

    def _process_message(self, text: str):
        if self._llm_thread and self._llm_thread.isRunning():
            return  # Debounce

        # Add user bubble
        self._add_bubble("user", text)

        # Update status
        self.orb.set_state(OrbState.THINKING)
        self._header_status.setText("Thinking...")

        # Create assistant bubble (streaming target)
        self._current_assistant_bubble = self._add_bubble("assistant", "")
        self._full_response = ""

        # Start LLM thread
        self._llm_thread = LLMThread(text)
        self._llm_thread.chunk_received.connect(self._on_chunk)
        self._llm_thread.finished.connect(self._on_response_done)
        self._llm_thread.error_occurred.connect(self._on_llm_error)
        self._llm_thread.start()

        logger.debug(f"User message: {text[:80]}")

    def _add_bubble(self, role: str, content: str) -> MessageBubble:
        """Add a message bubble to the chat."""
        # Wrapper for alignment
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)

        bubble = MessageBubble(role, content)
        bubble.setMaximumWidth(int(self._scroll.width() * 0.82))

        if role == "user":
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        wrapper_widget = QWidget()
        wrapper_widget.setLayout(wrapper)

        # Insert before the final stretch
        insert_idx = self._chat_layout.count() - 1
        self._chat_layout.insertWidget(insert_idx, wrapper_widget)

        # Auto-scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
        return bubble

    @Slot(str)
    def _on_chunk(self, chunk: str):
        if self._current_assistant_bubble:
            self._current_assistant_bubble.append_chunk(chunk)
            self._full_response += chunk
            QTimer.singleShot(10, self._scroll_to_bottom)

    @Slot(str)
    def _on_response_done(self, full_text: str):
        if self._current_assistant_bubble:
            self._current_assistant_bubble.set_full_content(full_text)
        self.orb.set_state(OrbState.IDLE)
        self._header_status.setText("AI Desktop Assistant  •  Ready")
        self._current_assistant_bubble = None
        logger.debug(f"Response complete ({len(full_text)} chars)")

        # Auto-save to memory
        try:
            from jarvis.memory.memory_manager import memory_manager
            last_user = ""
            for m in reversed(self._chat_history()):
                if m[0] == "user":
                    last_user = m[1]
                    break
            if last_user:
                memory_manager.add(
                    content=f"User: {last_user}\nJarvis: {full_text}",
                    memory_type="conversation"
                )
        except Exception:
            pass  # Memory system may not be initialized yet

    @Slot(str)
    def _on_llm_error(self, error: str):
        if self._current_assistant_bubble:
            self._current_assistant_bubble.set_full_content(
                f"⚠️ Error: {error}\n\nPlease check your API key in Settings."
            )
        self.orb.set_state(OrbState.ERROR)
        self._header_status.setText("Error — check settings")
        QTimer.singleShot(3000, lambda: self.orb.set_state(OrbState.IDLE))
        logger.error(f"LLM error: {error}")

    def _chat_history(self) -> list[tuple[str, str]]:
        from jarvis.core.brain import brain
        return [(m["role"], m["content"]) for m in brain.get_history()]

    def _scroll_to_bottom(self):
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _show_welcome(self):
        welcome = (
            "👋 Hello! I'm **Jarvis**, your AI desktop assistant.\n\n"
            "I can help you with:\n"
            "• 💬 **Answering questions** and having conversations\n"
            "• 🖥 **Controlling your computer** — open apps, manage files\n"
            "• 🌐 **Browsing the web** and summarizing pages\n"
            "• 📅 **Scheduling tasks** and setting reminders\n"
            "• 🧠 **Remembering** your preferences and past conversations\n\n"
            "To get started, set your API key in **Settings** (sidebar → Settings tab).\n"
            "Or try saying: *'Hey Jarvis'* to activate voice mode!"
        )
        self._add_bubble("assistant", welcome)

    # ── Shortcuts ─────────────────────────────────────────────────────
    def _setup_shortcuts(self):
        # Ctrl+Enter to send
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_shortcut.activated.connect(self._send_message)

        # Ctrl+N — new chat
        new_chat_sc = QShortcut(
            QKeySequence(config.get("shortcut_new_chat", "Ctrl+N")), self
        )
        new_chat_sc.activated.connect(self.new_chat)

        # F12 — dev console
        dev_sc = QShortcut(QKeySequence("F12"), self)
        dev_sc.activated.connect(self._show_dev_console)

    # ── Window actions ────────────────────────────────────────────────
    def new_chat(self):
        """Clear chat and start fresh."""
        from jarvis.core.brain import brain
        brain.clear_history()
        # Remove all widgets except the stretch
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._show_welcome()
        logger.info("New chat started")

    def open_settings(self):
        self._settings_window.show()
        self._settings_window.raise_()

    def _show_notifications(self):
        self._notifications.show()
        self._notifications.raise_()

    def _show_dev_console(self):
        self._dev_console.show()
        self._dev_console.raise_()

    def push_notification(self, title: str, body: str, priority: str = "normal"):
        self._notifications.add_notification(title, body, priority)

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")
