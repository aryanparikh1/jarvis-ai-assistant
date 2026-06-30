# ⚡ Jarvis AI Desktop Assistant

<div align="center">

![Jarvis Banner](assets/images/banner.png)

**A production-ready AI desktop assistant for Windows, inspired by Iron Man's J.A.R.V.I.S.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://pypi.org/project/PySide6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ Features

### 🧠 AI Powered
- **Multi-LLM support** — OpenAI GPT-4o, Google Gemini, Ollama (local)
- **Streaming responses** — real-time token-by-token output
- **ReAct agent loop** — multi-step reasoning with tool calls
- **Long-term memory** — SQLite + ChromaDB semantic search

### 🎤 Voice Assistant
- **Wake word** — "Hey Jarvis" via OpenWakeWord
- **STT** — faster-whisper (local, high accuracy)
- **TTS** — Microsoft Edge Neural voices (free, high quality)
- **Push-to-talk** — keyboard shortcut `Ctrl+Shift+Space`

### 🖥 Desktop Control
- Open, close, focus any application
- File CRUD — create, read, update, delete, search
- Volume, brightness, clipboard, media controls
- Screenshot capture
- Terminal command execution

### 🌐 Browser Automation
- Playwright-powered Chrome/Edge control
- Web search, webpage summarization
- Form filling, tab management
- Screenshot of web pages

### 📅 Productivity
- Task scheduler (one-shot, interval, cron)
- Reminders with Windows notifications
- Plugin system for custom extensions
- REST API for mobile app integration

### 🎨 UI/UX
- Dark glassmorphism design
- Animated AI orb (idle / listening / thinking / speaking)
- Animated microphone indicator
- System tray integration
- Developer console with live logs

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 / 11
- Python 3.11+
- Microphone + Speakers (for voice)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/aryanparikh415/jarvis-ai-assistant.git
cd jarvis-ai-assistant

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Run Jarvis
python main.py
```

### First-time Setup

1. Open **Settings** (sidebar → Settings)
2. Add your **OpenAI API key** (or Gemini / set up Ollama for free local AI)
3. Configure your preferred **voice**, **wake word**, and **shortcuts**
4. Optionally enable **Start with Windows** for background operation

---

## 📁 Project Structure

```
jarvis/
├── main.py                 # Entry point
├── requirements.txt        # All dependencies
├── jarvis/
│   ├── app.py              # QApplication bootstrap
│   ├── gui/                # All UI components
│   │   ├── main_window.py  # Main chat window
│   │   ├── voice_panel.py  # Voice interaction
│   │   ├── orb_widget.py   # Animated AI orb
│   │   └── ...
│   ├── core/
│   │   ├── brain.py        # LLM engine
│   │   ├── task_planner.py # ReAct planner
│   │   └── permission_system.py
│   ├── voice/
│   │   ├── wake_word.py    # OpenWakeWord
│   │   ├── stt.py          # faster-whisper
│   │   └── tts.py          # Edge-TTS
│   ├── agents/
│   │   ├── browser_agent.py
│   │   ├── desktop_agent.py
│   │   └── scheduler_agent.py
│   ├── memory/
│   │   └── memory_manager.py  # SQLite + ChromaDB
│   ├── tools/              # All tool implementations
│   ├── plugins/            # Plugin system
│   └── api/                # FastAPI REST server
├── config/                 # Configuration files
├── plugins/                # User-created plugins
└── data/                   # Runtime data (DB, ChromaDB)
```

---

## 🔧 Configuration

All settings are stored in `config/settings.json` and can be changed via the Settings UI.

Key settings:
| Setting | Default | Description |
|---|---|---|
| `llm_provider` | `openai` | `openai` / `gemini` / `ollama` |
| `wake_word` | `hey jarvis` | Wake word phrase |
| `whisper_model` | `base` | `tiny/base/small/medium/large` |
| `tts_voice` | `en-US-AriaNeural` | Edge-TTS voice |
| `api_enabled` | `false` | Enable REST API server |
| `api_port` | `8765` | REST API port |

---

## 🎮 Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+J` | Show / Hide Jarvis |
| `Ctrl+Shift+Space` | Push-to-Talk |
| `Ctrl+N` | New Chat |
| `Ctrl+Enter` | Send message |
| `F12` | Developer Console |

---

## 🔌 Plugin Development

Create a file in the `plugins/` folder:

```python
from jarvis.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    description = "Does something awesome"
    version = "1.0.0"
    author = "You"

    def on_load(self):
        print("Plugin loaded!")

    def on_unload(self):
        print("Plugin unloaded!")

    def on_message(self, message: str) -> str | None:
        if "hello" in message.lower():
            return "Hello from my plugin!"
        return None  # Let other handlers process it
```

---

## 🌐 REST API

When enabled (`api_enabled: true` in settings), Jarvis exposes a REST API:

```bash
# Chat
POST http://localhost:8765/chat
{"message": "What is the weather in London?"}

# Execute tool
POST http://localhost:8765/tools/execute
{"tool_name": "get_current_time", "args": {}}

# Search memory
GET http://localhost:8765/memory/search?q=my+preference

# API docs
GET http://localhost:8765/docs
```

---

## 🏗 Building as .exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icons/jarvis.ico \
  --add-data "jarvis/gui/styles;jarvis/gui/styles" \
  --add-data "config;config" \
  --add-data "assets;assets" \
  main.py
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────┐
│              GUI Layer (PySide6)             │
│  MainWindow | VoicePanel | TaskDashboard    │
│  MemoryUI | SystemTray | DevConsole         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            Core Agent Layer                  │
│  LLMBrain | TaskPlanner | PermissionSystem  │
└──────┬──────────────────────────────────────┘
       │
┌──────▼─────────────────────────────────────┐
│           Specialized Agents                │
│  BrowserAgent | DesktopAgent | Scheduler   │
└──────┬─────────────────────────────────────┘
       │
┌──────▼─────────────────────────────────────┐
│            Infrastructure                   │
│  SQLite + ChromaDB | Plugins | FastAPI     │
└────────────────────────────────────────────┘
```

---

## 🔒 Permission System

| Level | Examples | Behavior |
|---|---|---|
| ✅ Safe | Web search, read files, open apps | Auto-execute |
| ⚠️ Medium | Write files, fill forms, schedule tasks | Ask once per session |
| 🚨 Dangerous | Delete files, run commands, kill processes | Always confirm |

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**Aryan Parikh** — aryanparikh415@gmail.com

---

*Built with ❤️ and ⚡ — Just A Rather Very Intelligent System*
