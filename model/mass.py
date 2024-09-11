import json
import sys

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMainWindow, QHBoxLayout, QFrame, QApplication, QLineEdit, QPushButton, \
    QDateEdit, QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog

from model.mass_elements import Bible, MassMoment, Librone, Pages
from model.rfixed_rites import *

from qt_material import apply_stylesheet

casi_duso = """

# BASE
- Download dicitura tempo ordinario e messa + data
- Accetta di non trovare la seconda lettura in settimana

- Paginazione più smart, canti (strofa + RIT in pagina), letture (wpp 150), fixed (wpp 100)

- CANTO santo (momento messa, canto in Librone, selezione Launcher)

- TASTO PER aggiungere immagine volante/predefinita, solitamente alla fine
- TASTO PER aggiungere canzone volante, poco prima della messa, ma anche durante prendendo spunto dall'omelia
- TASI +/- per resize del font

- librone su drive, scaricare canzoni in fase di creazione nel file .json

# EXTRA
- canti con doppie voci
- sequenze particolari (sequenza pasquale,)
"""


class Mass(QMainWindow):
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


class Launcher(QMainWindow):
    def __init__(self, file_librone="librone.json"):
        super().__init__()

        self.messa = None
        self.date = ""
        self.bible = Bible()
        self.librone = Librone("../librone.json")
        self.songs_by_moment = self.librone.load_songs_by_moment()

        main_layout = QVBoxLayout()
        main_frame = QFrame()

        load_layout = QHBoxLayout()
        self.txt_filename = QLineEdit()
        self.txt_filename.setEnabled(False)
        btn_pick_file = QPushButton('...')
        btn_pick_file.clicked.connect(self.on_pick_file)
        self.btn_start = QPushButton(' INIZIA MESSA!')
        self.btn_start.setIcon(QIcon("../start.png"))
        self.btn_start.clicked.connect(self.on_start_messa)
        self.btn_start.setEnabled(False)
        load_layout.addWidget(self.txt_filename)
        load_layout.addWidget(btn_pick_file)
        load_layout.addWidget(self.btn_start)

        new_layout = QHBoxLayout()
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate(2024, 9, 1))
        btn_save = QPushButton('Salva Messa')
        btn_save.clicked.connect(self.on_save_messa)
        new_layout.addWidget(self.date_edit)
        new_layout.addWidget(btn_save)

        lbl_canto_text = {
            MassMoment.intro: "Ingresso",
            MassMoment.gloria: "Gloria",
            MassMoment.offertorio: "Offertorio",
            MassMoment.pace: "Pace",
            MassMoment.comunione: "Comunione",
            MassMoment.fine: "Uscita"
        }

        self.list_songs = {}

        layout_songs = QHBoxLayout()

        for mom, head in lbl_canto_text.items():
            ly = QVBoxLayout()
            lbl = QLabel(f"<b>{head}:</b>")
            self.list_songs[mom] = QListWidget()
            for title in self.songs_by_moment[mom]:
                self.list_songs[mom].addItem(QListWidgetItem(title))
            self.list_songs[mom].setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            ly.addWidget(lbl)
            ly.addWidget(self.list_songs[mom])

            layout_songs.addLayout(ly)

        main_layout.addLayout(new_layout)
        main_layout.addLayout(layout_songs)
        main_layout.addLayout(load_layout)

        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)

    def on_start_messa(self):
        # Set and configure the messa
        self.messa = Mass(aaaammdd=self.date)
        self.messa.set_bible(self.bible)
        self.messa.set_librone(self.librone)
        self.messa.showMaximized()

    def on_pick_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '../messe')[0]
        self.txt_filename.setText(fname)

        # Load the schema
        with open(fname, 'r') as f:
            messa_js = json.load(f)

        # Set the date
        self.date = messa_js['date']

        # Load lectures
        self.bible.load_json(messa_js['lectures'])

        # Load songs
        scaletta = {}
        for moment_name, song_list in messa_js['songs'].items():
            scaletta[MassMoment.from_name(moment_name)] = song_list
        self.librone.load_songs(scaletta)

        self.btn_start.setEnabled(True)

    def on_save_messa(self):
        scaletta = {}
        for moment, ls in self.list_songs.items():
            scaletta[moment] = [it.text() for it in ls.selectedItems()]
        self.librone.load_songs(scaletta)
        songs = {mom.name: value for (mom, value) in scaletta.items()}

        self.date = self.date_edit.date().toString("yyyyMMdd")
        self.bible.fetch_online(aaaammdd=self.date)

        lectures = {}
        for moment, lect in self.bible.lectures.items():
            lectures[moment.name] = lect.to_json()

        messa_js = {
            "date": self.date,
            "songs": songs,
            "lectures": lectures
        }

        with open(f'../messe/messa_{self.date}.json', 'w', encoding="utf-8") as outfile:
            json.dump(messa_js, outfile, indent=4)

        self.btn_start.setEnabled(True)



stylesheet = {
    # Button colors
    'danger': '#dc3545',
    'warning': '#ffc107',
    'success': '#13191c',
    # Font
    'font_family': 'Roboto',
    'background': '#202020',
}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_lightgreen.xml', invert_secondary=False,
                     extra=stylesheet, css_file="custom.css")

    # create the instance of our Window
    # window = Mass(aaaammdd="20240908")
    window = Launcher()
    window.showMaximized()

    # start the app
    sys.exit(app.exec())
