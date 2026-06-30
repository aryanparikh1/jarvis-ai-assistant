"""Notification Agent — Windows toast notifications."""
from PySide6.QtCore import QObject, Signal
from jarvis.utils.logger import logger

class NotificationAgent(QObject):
    notification_sent = Signal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
    def notify(self, title: str, body: str, priority: str = "normal"):
        logger.info(f"Notification: [{priority}] {title} — {body}")
        self.notification_sent.emit(title, body)
        try:
            from plyer import notification
            notification.notify(title=title, message=body, app_name="Jarvis", timeout=5)
        except Exception as e:
            logger.warning(f"Notification error: {e}")

notification_agent = NotificationAgent()
