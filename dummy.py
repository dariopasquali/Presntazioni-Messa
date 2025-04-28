from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtCore import Qt, QTimer
import re  # For regex replacement


class AutoFontLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        # self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_text = text
        self.setStyleSheet("color: white; background-color: black;")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def setText(self, text):
        # Replace multiple <br><br> with a custom identifier or normal breaks
        self.original_text = self.processText(text)
        super().setText(self.original_text)
        self.adjustFontSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustFontSize()

    def processText(self, text):
        # Replace multiple <br><br> with \n to ensure proper line breaks
        # text = re.sub(r'(<br><br>)+', r'\n\n', text)
        return text

    def adjustFontSize(self):
        if not self.original_text:
            return

        label_width = self.width()
        label_height = self.height()

        if label_width == 0 or label_height == 0:
            return

        min_size = 5
        max_size = 300
        margin_per_br = 0.1  # This represents the added margin per <br><br> (in font-size proportions)

        font = self.font()
        best_size = min_size
        metrics = None

        # Count the number of occurrences of \n\n (equivalent to <br><br> in the processed text)
        double_br_count = self.original_text.count('<br><br>')

        # Adjust the available height to account for vertical spacing
        adjusted_height = int(label_height - (double_br_count * margin_per_br * label_height))

        for size in range(min_size, max_size + 1):
            font.setPointSize(size)
            self.setFont(font)
            metrics = QFontMetrics(font)

            # Calculate the size of the text, including line breaks
            text_rect = metrics.boundingRect(
                0, 0, label_width, adjusted_height,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self.original_text
            )

            # Add some margin to prevent clipping
            if text_rect.width() > label_width or text_rect.height() > adjusted_height:
                break

            best_size = size

        # Set the optimal font size
        font.setPointSize(best_size)
        self.setFont(font)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(20, 20, 20, 20)  # 20px margin

    # Example with <br><br> line breaks (double newlines)
    text = """<p style="margin-bottom: 25px;"><b>Grandi cose ha fatto il Signore per noi,<br>ha fatto germogliare i fiori fra le rocce.<br>Grandi cose ha fatto il Signore per noi,<br>ci ha riportati liberi alla nostra terra.<br>Ed ora possiamo cantare, possiamo gridare<br>l'amore che Dio ha versato su noi.</b></p><p style="margin-bottom: 25px;">Tu che sai strappare dalla morte,<br>hai sollevato il nostro viso dalla polvere.<br>Tu che hai sentito il nostro pianto,<br>nel nostro cuore hai messo un seme di felicità.</p>"""

    label = AutoFontLabel(text)
    layout.addWidget(label)

    window.setWindowTitle("Full Screen Example")
    window.showFullScreen()

    # Adjust font size after the window has been displayed
    QTimer.singleShot(100, label.adjustFontSize)

    sys.exit(app.exec())
