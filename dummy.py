from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtCore import Qt, QSize
import sys

class AutoFontLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.original_text = text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()

    def adjustFontSize(self):
        if not self.original_text:
            return

        # Get size of label
        rect = self.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        font = self.font()
        font_size = 1
        font.setPointSize(font_size)
        self.setFont(font)

        metrics = QFontMetrics(font)
        while True:
            new_font = QFont(font)
            new_font.setPointSize(font_size + 1)
            new_metrics = QFontMetrics(new_font)

            if (new_metrics.boundingRect(self.original_text).width() > rect.width() or
                new_metrics.boundingRect(self.original_text).height() > rect.height()):
                break

            font_size += 1
            font = new_font

        self.setFont(font)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.label = AutoFontLabel("Resizable Font Label")
        self.setCentralWidget(self.label)
        self.setMinimumSize(QSize(200, 100))

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
