# ui.py - UI components and dialogs for AnkiScape

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
import os

# UI Classes
class ExpPopup(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: rgba(70, 130, 180, 200);
            color: white;
            border-radius: 10px;
            padding: 5px;
            font-weight: bold;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show_exp(self, exp):
        self.setText(f"+{exp} XP")
        self.adjustSize()
        self.show()
        self.move(self.parent().width() - self.width() - 20, self.parent().height() - 100)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self.hide)
        self.float_animation = QPropertyAnimation(self, b"pos")
        self.float_animation.setDuration(2000)
        start_pos = self.pos()
        end_pos = start_pos - QPoint(0, 50)
        self.float_animation.setStartValue(start_pos)
        self.float_animation.setEndValue(end_pos)
        self.float_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()
        self.float_animation.start()

# UI Functions
# ...existing code...
# Move all dialog, popup, and menu functions here from __init__.py
