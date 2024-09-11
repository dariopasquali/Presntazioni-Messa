import json
import sys

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMainWindow, QHBoxLayout, QFrame, QApplication, QLineEdit, QPushButton, \
    QDateEdit, QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog

from model.bible import Bible
from model.librone import Librone
from model.commons import MassMoment, Pages
from model.rfixed_rites import *

from qt_material import apply_stylesheet

casi_duso = """

# BASE
- Eseguibile

- Download dicitura tempo ordinario e messa + data
- Paginazione più smart, canti (strofa + RIT in pagina), letture (wpp 150), fixed (wpp 100)

- TASTO PER aggiungere immagine volante/predefinita, solitamente alla fine
- TASTO PER aggiungere canzone volante, poco prima della messa, ma anche durante prendendo spunto dall'omelia
- TASI +/- per resize del font

- librone su drive, scaricare canzoni in fase di creazione nel file .json

# EXTRA
- canti con doppie voci
- sequenze particolari (sequenza pasquale,)
"""


class MassPresenter(QMainWindow):
    def __init__(self, aaaammdd):
        super().__init__()
        self.date = aaaammdd
        self.bible = None
        self.librone = None

        self.mass_moment_pointer = 0
        self.sequence = [
            MassMoment.welcome,
            MassMoment.intro,
            MassMoment.silence,

            MassMoment.confesso,
            MassMoment.silence,

            MassMoment.kyrie,
            MassMoment.silence,

            MassMoment.gloria,
            MassMoment.silence,

            MassMoment.lettura_1,
            MassMoment.salmo,
            MassMoment.lettura_2,
            MassMoment.alleluia,
            MassMoment.vangelo,
            MassMoment.silence,

            MassMoment.credo,
            MassMoment.silence,

            MassMoment.offertorio,
            MassMoment.silence,

            MassMoment.santo,
            MassMoment.silence,

            MassMoment.padre_nostro,
            MassMoment.padre_nostro,

            MassMoment.pace,
            MassMoment.silence,

            MassMoment.agnello,
            MassMoment.silence,

            MassMoment.invito_cena,
            MassMoment.silence,

            MassMoment.comunione,
            MassMoment.silence,

            MassMoment.fine]

        self.mass_structure = {
            MassMoment.intro: [],  # C
            MassMoment.confesso: [Pages(body=confesso)],  # R
            MassMoment.kyrie: [Pages(body=kyrie)],  # R
            MassMoment.gloria: [],  # C
            MassMoment.lettura_1: [],  # L
            MassMoment.salmo: [],  # L
            MassMoment.lettura_2: [],  # L
            MassMoment.alleluia: [],  # L
            MassMoment.vangelo: [],  # L
            MassMoment.credo: [Pages(body=credo_apostolico)],  # R
            MassMoment.offertorio: [],  # C
            MassMoment.santo: [],       # TODO
            MassMoment.padre_nostro: [Pages(body=padre_nostro)],  # R
            MassMoment.pace: [],  # C
            MassMoment.agnello: [Pages(body=agnello)],  # R
            MassMoment.invito_cena: [Pages(body=invito_cena)],  # R
            MassMoment.comunione: [],  # C
            MassMoment.fine: [],  # C
        }

        self.setWindowTitle(f'Messa del {aaaammdd}')
        main_layout = QHBoxLayout()
        main_frame = QFrame()

        self.body = QLabel(f'Messa del {aaaammdd}')
        # self.body.setStyleSheet("font-size: 45pt;")
        self.body.setFont(QFont("Roboto", 50))
        self.body.setWordWrap(True)
        self.body.setContentsMargins(20, 0, 20, 0)
        self.body.setProperty('class', 'main_label')

        main_layout.addWidget(self.body)
        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)
        self.setFocus()

        self.page_pointer = -1
        self.pages = []
        self.words_per_page = 90

    def set_bible(self, bible):
        self.bible = bible
        self.mass_structure[MassMoment.lettura_1] = [self.bible.get(MassMoment.lettura_1)]  # L
        self.mass_structure[MassMoment.salmo] = [self.bible.get(MassMoment.salmo)]  # L
        self.mass_structure[MassMoment.lettura_2] = [self.bible.get(MassMoment.lettura_2)]  # L
        self.mass_structure[MassMoment.alleluia] = [self.bible.get(MassMoment.alleluia)]  # L
        self.mass_structure[MassMoment.vangelo] = [self.bible.get(MassMoment.vangelo)]  # L


    def set_librone(self, librone):
        self.librone = librone
        self.mass_structure[MassMoment.intro] = self.librone.get(MassMoment.intro)  # C
        self.mass_structure[MassMoment.gloria] = self.librone.get(MassMoment.gloria)  # C
        self.mass_structure[MassMoment.offertorio] = self.librone.get(MassMoment.offertorio)  # C
        self.mass_structure[MassMoment.santo] = self.librone.get(MassMoment.santo)  # C
        self.mass_structure[MassMoment.pace] = self.librone.get(MassMoment.pace)  # C
        self.mass_structure[MassMoment.comunione] = self.librone.get(MassMoment.comunione)  # C
        self.mass_structure[MassMoment.fine] = self.librone.get(MassMoment.fine)  # C


    def load_songs(self, mass_moment, song):
        self.mass_structure[mass_moment].append(song)

    def paginate(self, txt):
        words = txt.split(" ")
        return [" ".join(words[i:i + self.words_per_page]) for i in range(0, len(words), self.words_per_page)]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.on_left()
        elif event.key() == Qt.Key.Key_Right:
            self.on_right()

    def resizeEvent(self, event):
        """Automatically adjust the font size based on the window's width."""
        self.adjust_font_size()
        super().resizeEvent(event)  # Call the parent's resizeEvent

    def adjust_font_size(self):
        """Adjust font size dynamically based on window width."""
        # Get the width of the window
        window_h = self.height()

        # Adjust font size based on the window width
        # You can fine-tune this scaling factor as needed
        font_size = window_h // 28

        # Set the new font size
        font = self.body.font()
        font.setPointSize(font_size)
        self.body.setFont(font)

    def on_left(self):
        self.page_pointer -= 1
        if self.page_pointer < 0:
            # Previous Section
            self.mass_moment_pointer = max(0, self.mass_moment_pointer - 1)
            mass_el = self.sequence[self.mass_moment_pointer]
            if mass_el == MassMoment.welcome:
                self.page_pointer = 0
                self.mass_moment_pointer = 1
                return

            if mass_el == MassMoment.silence:
                self.pages = [""]

            elif len(self.mass_structure[mass_el]) == 0:
                self.pages = [f"TODO {mass_el.name}"]
            else:
                self.pages = []
                for el in self.mass_structure[mass_el]:
                    for p in el.get_pages(wpp=self.words_per_page):
                        self.pages.append(p)

            self.page_pointer = len(self.pages) - 1

        self.body.setText(self.pages[self.page_pointer])
        self.adjust_font_size()

    def on_right(self):
        self.page_pointer += 1
        if self.page_pointer >= len(self.pages):
            # Next Section
            self.mass_moment_pointer = min(len(self.sequence), self.mass_moment_pointer + 1)
            if self.mass_moment_pointer == len(self.sequence):
                sys.exit(0)
            mass_el = self.sequence[self.mass_moment_pointer]

            if mass_el == MassMoment.silence:
                self.pages = [""]

            elif len(self.mass_structure[mass_el]) == 0:
                self.pages = [f"TODO {mass_el.name}"]
            else:
                self.pages = []
                for el in self.mass_structure[mass_el]:
                    for p in el.get_pages(wpp=self.words_per_page):
                        self.pages.append(p)

            self.page_pointer = 0

        self.body.setText(self.pages[self.page_pointer])
        self.adjust_font_size()

    def add(self, mass_moment, song):
        self.mass_structure[mass_moment].append(song)



