import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QFontDatabase, QFont

class CustomFontApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Font Example")

        label = QLabel("This text uses a custom font!")

        # Load the custom font
        font_id = QFontDatabase.addApplicationFont("fonts/Roboto-Black.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                custom_font = QFont(font_families[0], 16)
                label.setFont(custom_font)
            else:
                label.setText("Font loaded, but no family found.")
        else:
            label.setText("Failed to load custom font.")

        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomFontApp()
    window.show()
    sys.exit(app.exec())
