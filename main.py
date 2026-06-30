"""
Jarvis AI Desktop Assistant — Entry Point
==========================================
Run with:  python main.py
Build exe: pyinstaller --onefile --windowed --icon=assets/icons/jarvis.ico main.py
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis.app import JarvisApplication


def main():
    app = JarvisApplication(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
