"""
Settings Window
================
Full settings dialog covering all Jarvis configuration categories:
  - General / Appearance
  - LLM Provider
  - Voice
  - Memory
  - Permissions
  - Startup & Shortcuts
"""

import keyring
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSlider, QGroupBox, QFormLayout, QFrame, QSpinBox,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from jarvis.utils.config import config
from jarvis.utils.logger import logger
from jarvis.utils.startup import register_startup, unregister_startup, is_registered


class SettingsWindow(QDialog):
    """Comprehensive settings dialog."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙  Jarvis Settings")
        self.setMinimumSize(640, 580)
        self.resize(720, 640)
        self._build_ui()
        self._load_values()

    # ── UI Build ──────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)

        title = QLabel("SETTINGS")
        title.setObjectName("sectionHeader")
        layout.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "🖥  General")
        self._tabs.addTab(self._build_llm_tab(), "🧠  AI Model")
        self._tabs.addTab(self._build_voice_tab(), "🎤  Voice")
        self._tabs.addTab(self._build_memory_tab(), "🧠  Memory")
        self._tabs.addTab(self._build_shortcuts_tab(), "⌨  Shortcuts")
        layout.addWidget(self._tabs)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        btn_box.accepted.connect(self._save)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore_defaults
        )
        layout.addWidget(btn_box)

    # ── Tabs ──────────────────────────────────────────────────────────
    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        # Appearance group
        appear = QGroupBox("Appearance")
        form = QFormLayout(appear)
        self._accent_color = QLineEdit()
        self._accent_color.setPlaceholderText("#00D4FF")
        form.addRow("Accent Color:", self._accent_color)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(50, 100)
        self._opacity_slider.setValue(95)
        form.addRow("Window Opacity (%):", self._opacity_slider)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 16)
        self._font_size.setValue(10)
        form.addRow("Font Size (pt):", self._font_size)
        layout.addWidget(appear)

        # Startup group
        startup = QGroupBox("Startup")
        sform = QFormLayout(startup)
        self._start_minimized = QCheckBox("Start minimized to tray")
        sform.addRow(self._start_minimized)
        self._start_on_boot = QCheckBox("Start Jarvis with Windows")
        sform.addRow(self._start_on_boot)
        layout.addWidget(startup)

        # Notifications
        notif = QGroupBox("Notifications")
        nform = QFormLayout(notif)
        self._notif_enabled = QCheckBox("Enable notifications")
        nform.addRow(self._notif_enabled)
        self._notif_sound = QCheckBox("Play notification sound")
        nform.addRow(self._notif_sound)
        layout.addWidget(notif)

        layout.addStretch()
        return w

    def _build_llm_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        provider = QGroupBox("AI Provider")
        form = QFormLayout(provider)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(["openai", "gemini", "ollama"])
        form.addRow("Provider:", self._provider_combo)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)

        # OpenAI
        self._openai_key = QLineEdit()
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key.setPlaceholderText("sk-...")
        form.addRow("OpenAI API Key:", self._openai_key)

        self._openai_model = QComboBox()
        self._openai_model.addItems(["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"])
        form.addRow("OpenAI Model:", self._openai_model)

        # Gemini
        self._gemini_key = QLineEdit()
        self._gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._gemini_key.setPlaceholderText("AIza...")
        form.addRow("Gemini API Key:", self._gemini_key)

        self._gemini_model = QComboBox()
        self._gemini_model.addItems([
            "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"
        ])
        form.addRow("Gemini Model:", self._gemini_model)

        # Ollama
        self._ollama_host = QLineEdit()
        self._ollama_host.setPlaceholderText("http://localhost:11434")
        form.addRow("Ollama Host:", self._ollama_host)

        self._ollama_model = QLineEdit()
        self._ollama_model.setPlaceholderText("llama3")
        form.addRow("Ollama Model:", self._ollama_model)

        layout.addWidget(provider)

        # Parameters
        params = QGroupBox("Generation Parameters")
        pform = QFormLayout(params)

        self._temperature = QSlider(Qt.Orientation.Horizontal)
        self._temperature.setRange(0, 100)
        self._temperature.setValue(70)
        pform.addRow("Temperature (0-1):", self._temperature)

        self._max_tokens = QSpinBox()
        self._max_tokens.setRange(256, 8192)
        self._max_tokens.setSingleStep(256)
        self._max_tokens.setValue(2048)
        pform.addRow("Max Tokens:", self._max_tokens)

        layout.addWidget(params)

        # System prompt
        sys_prompt = QGroupBox("System Prompt")
        sp_layout = QVBoxLayout(sys_prompt)
        from PySide6.QtWidgets import QPlainTextEdit
        self._system_prompt = QPlainTextEdit()
        self._system_prompt.setMaximumHeight(120)
        self._system_prompt.setPlaceholderText("You are Jarvis...")
        sp_layout.addWidget(self._system_prompt)
        layout.addWidget(sys_prompt)

        layout.addStretch()
        return w

    def _build_voice_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        ww = QGroupBox("Wake Word")
        wwform = QFormLayout(ww)
        self._voice_enabled = QCheckBox("Enable voice assistant")
        wwform.addRow(self._voice_enabled)
        self._wake_word = QLineEdit()
        self._wake_word.setPlaceholderText("hey jarvis")
        wwform.addRow("Wake Word:", self._wake_word)
        self._ww_sensitivity = QSlider(Qt.Orientation.Horizontal)
        self._ww_sensitivity.setRange(1, 10)
        self._ww_sensitivity.setValue(5)
        wwform.addRow("Sensitivity (1-10):", self._ww_sensitivity)
        layout.addWidget(ww)

        stt = QGroupBox("Speech to Text (STT)")
        sttform = QFormLayout(stt)
        self._stt_backend = QComboBox()
        self._stt_backend.addItems(["whisper", "google"])
        sttform.addRow("Backend:", self._stt_backend)
        self._whisper_model = QComboBox()
        self._whisper_model.addItems(["tiny", "base", "small", "medium", "large"])
        sttform.addRow("Whisper Model:", self._whisper_model)
        layout.addWidget(stt)

        tts = QGroupBox("Text to Speech (TTS)")
        ttsform = QFormLayout(tts)
        self._tts_backend = QComboBox()
        self._tts_backend.addItems(["edge", "pyttsx3"])
        ttsform.addRow("Backend:", self._tts_backend)
        self._tts_voice = QComboBox()
        self._tts_voice.addItems([
            "en-US-AriaNeural", "en-US-GuyNeural",
            "en-GB-SoniaNeural", "en-AU-NatashaNeural"
        ])
        ttsform.addRow("Voice:", self._tts_voice)
        layout.addWidget(tts)

        layout.addStretch()
        return w

    def _build_memory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        mem = QGroupBox("Memory Settings")
        mform = QFormLayout(mem)
        self._memory_enabled = QCheckBox("Enable long-term memory")
        mform.addRow(self._memory_enabled)
        self._auto_extract = QCheckBox("Auto-extract memories from conversations")
        mform.addRow(self._auto_extract)
        self._max_context = QSpinBox()
        self._max_context.setRange(5, 100)
        self._max_context.setValue(20)
        mform.addRow("Max context messages:", self._max_context)

        clear_mem_btn = QPushButton("🗑  Clear All Memories")
        clear_mem_btn.setObjectName("dangerBtn")
        clear_mem_btn.clicked.connect(self._clear_memories)
        mform.addRow(clear_mem_btn)
        layout.addWidget(mem)

        layout.addStretch()
        return w

    def _build_shortcuts_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        sc = QGroupBox("Keyboard Shortcuts")
        scform = QFormLayout(sc)
        self._sc_show_hide = QLineEdit()
        self._sc_show_hide.setPlaceholderText("ctrl+shift+j")
        scform.addRow("Show/Hide Jarvis:", self._sc_show_hide)
        self._sc_ptt = QLineEdit()
        self._sc_ptt.setPlaceholderText("ctrl+shift+space")
        scform.addRow("Push-to-Talk:", self._sc_ptt)
        self._sc_new_chat = QLineEdit()
        self._sc_new_chat.setPlaceholderText("ctrl+n")
        scform.addRow("New Chat:", self._sc_new_chat)
        layout.addWidget(sc)

        api = QGroupBox("REST API Server")
        aform = QFormLayout(api)
        self._api_enabled = QCheckBox("Enable API server")
        aform.addRow(self._api_enabled)
        self._api_port = QSpinBox()
        self._api_port.setRange(1024, 65535)
        self._api_port.setValue(8765)
        aform.addRow("Port:", self._api_port)
        layout.addWidget(api)

        layout.addStretch()
        return w

    # ── Load / Save ───────────────────────────────────────────────────
    def _load_values(self):
        self._accent_color.setText(config.get("accent_color", "#00D4FF"))
        self._opacity_slider.setValue(int(config.get("opacity", 0.95) * 100))
        self._font_size.setValue(config.get("font_size", 10))
        self._start_minimized.setChecked(config.get("start_minimized", False))
        self._start_on_boot.setChecked(is_registered())
        self._notif_enabled.setChecked(config.get("notifications_enabled", True))
        self._notif_sound.setChecked(config.get("notification_sound", True))

        provider = config.get("llm_provider", "openai")
        idx = self._provider_combo.findText(provider)
        self._provider_combo.setCurrentIndex(max(0, idx))

        # Load API keys from keyring
        self._openai_key.setText(keyring.get_password("jarvis", "openai_api_key") or "")
        self._gemini_key.setText(keyring.get_password("jarvis", "gemini_api_key") or "")

        self._openai_model.setCurrentText(config.get("openai_model", "gpt-4o-mini"))
        self._gemini_model.setCurrentText(config.get("gemini_model", "gemini-2.0-flash"))
        self._ollama_host.setText(config.get("ollama_host", "http://localhost:11434"))
        self._ollama_model.setText(config.get("ollama_model", "llama3"))
        self._temperature.setValue(int(config.get("temperature", 0.7) * 100))
        self._max_tokens.setValue(config.get("max_tokens", 2048))
        self._system_prompt.setPlainText(config.get("system_prompt", ""))

        self._voice_enabled.setChecked(config.get("voice_enabled", True))
        self._wake_word.setText(config.get("wake_word", "hey jarvis"))
        self._ww_sensitivity.setValue(int(config.get("wake_word_sensitivity", 0.5) * 10))
        self._stt_backend.setCurrentText(config.get("stt_backend", "whisper"))
        self._whisper_model.setCurrentText(config.get("whisper_model", "base"))
        self._tts_backend.setCurrentText(config.get("tts_backend", "edge"))
        self._tts_voice.setCurrentText(config.get("tts_voice", "en-US-AriaNeural"))

        self._memory_enabled.setChecked(config.get("memory_enabled", True))
        self._auto_extract.setChecked(config.get("auto_extract_memories", True))
        self._max_context.setValue(config.get("memory_max_context", 20))

        self._sc_show_hide.setText(config.get("shortcut_show_hide", "ctrl+shift+j"))
        self._sc_ptt.setText(config.get("shortcut_push_to_talk", "ctrl+shift+space"))
        self._sc_new_chat.setText(config.get("shortcut_new_chat", "ctrl+n"))
        self._api_enabled.setChecked(config.get("api_enabled", False))
        self._api_port.setValue(config.get("api_port", 8765))

    def _save(self):
        # Securely store API keys
        oai_key = self._openai_key.text().strip()
        if oai_key:
            keyring.set_password("jarvis", "openai_api_key", oai_key)
        gem_key = self._gemini_key.text().strip()
        if gem_key:
            keyring.set_password("jarvis", "gemini_api_key", gem_key)

        # Handle startup registration
        should_start = self._start_on_boot.isChecked()
        if should_start:
            register_startup()
        else:
            unregister_startup()

        config.update({
            "accent_color": self._accent_color.text() or "#00D4FF",
            "opacity": self._opacity_slider.value() / 100,
            "font_size": self._font_size.value(),
            "start_minimized": self._start_minimized.isChecked(),
            "start_on_boot": should_start,
            "notifications_enabled": self._notif_enabled.isChecked(),
            "notification_sound": self._notif_sound.isChecked(),
            "llm_provider": self._provider_combo.currentText(),
            "openai_model": self._openai_model.currentText(),
            "gemini_model": self._gemini_model.currentText(),
            "ollama_host": self._ollama_host.text(),
            "ollama_model": self._ollama_model.text(),
            "temperature": self._temperature.value() / 100,
            "max_tokens": self._max_tokens.value(),
            "system_prompt": self._system_prompt.toPlainText(),
            "voice_enabled": self._voice_enabled.isChecked(),
            "wake_word": self._wake_word.text(),
            "wake_word_sensitivity": self._ww_sensitivity.value() / 10,
            "stt_backend": self._stt_backend.currentText(),
            "whisper_model": self._whisper_model.currentText(),
            "tts_backend": self._tts_backend.currentText(),
            "tts_voice": self._tts_voice.currentText(),
            "memory_enabled": self._memory_enabled.isChecked(),
            "auto_extract_memories": self._auto_extract.isChecked(),
            "memory_max_context": self._max_context.value(),
            "shortcut_show_hide": self._sc_show_hide.text(),
            "shortcut_push_to_talk": self._sc_ptt.text(),
            "shortcut_new_chat": self._sc_new_chat.text(),
            "api_enabled": self._api_enabled.isChecked(),
            "api_port": self._api_port.value(),
        })

        self.settings_changed.emit()
        logger.info("Settings saved")
        self.accept()

    def _restore_defaults(self):
        reply = QMessageBox.question(
            self, "Restore Defaults",
            "Reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            config.reset_to_defaults()
            self._load_values()
            logger.info("Settings restored to defaults")

    def _clear_memories(self):
        reply = QMessageBox.warning(
            self, "Clear Memories",
            "This will delete ALL memories. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from jarvis.memory.memory_manager import memory_manager
                memory_manager.clear_all()
                QMessageBox.information(self, "Done", "All memories cleared.")
            except Exception as e:
                logger.error(f"Failed to clear memories: {e}")

    def _on_provider_changed(self, provider: str):
        pass  # Could show/hide relevant fields
