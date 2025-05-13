from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import sys

class Demo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        label_plain = QLabel("Plain text:\nLine A\nLine B")
        layout.addWidget(label_plain)

        label_html = QLabel("<b>HTML mode:</b><br>Line A\nLine B")
        layout.addWidget(label_html)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.resize(400, 200)
    w.show()
    sys.exit(app.exec())
