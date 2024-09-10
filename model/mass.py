import json
import sys

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMainWindow, QHBoxLayout, QFrame, QApplication, QLineEdit, QPushButton, \
    QDateEdit, QListWidget, QListWidgetItem, QAbstractItemView

from model.mass_elements import Bible, MassMoment, Librone, Pages
from model.rfixed_rites import *

from qt_material import apply_stylesheet

casi_duso = """
- aggiungere immagine volante/predefinita, solitamente alla fine
- aggiungere canzone volante, poco prima della messa, ma anche durante prendendo spunto dall'omelia
- testo nuovo, di canzone già, serve aggiongerlo al librone
- librone su drive
- file .messa con già tutto, canti e testi, scaricati in fase di creazione
- santo
- sequenze particolari (sequenza pasquale,)
- canti con doppie voci
- resize del font con +/-
- dicitura tempo ordinario e messa + data (download da lachiesa)
- accetta di non trovare la seconda lettura
"""


class Mass(QMainWindow):
    def __init__(self, aaaammdd):
        super().__init__()
        self.date = aaaammdd
        self.bible = Bible(aaaammdd=aaaammdd)
        self.librone = Librone("../librone.json")
        self.librone.load_songs(scaletta={
            MassMoment.intro: ["Chiamati per nome"],  # C
            MassMoment.gloria: ["Gloria Mariano"],  # C
            MassMoment.offertorio: ["Cosa offrirti"],  # C
            MassMoment.pace: ["La pace del Signore sia con te"],  # C
            MassMoment.comunione: ["Abbracciami"],  # C
            MassMoment.fine: ["Ora vado sulla mia strada"],  # C
        })

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
            MassMoment.intro: self.librone.get(MassMoment.intro),  # C

            MassMoment.confesso: [Pages(body=confesso)],  # R
            MassMoment.kyrie: [Pages(body=kyrie)],  # R

            MassMoment.gloria: self.librone.get(MassMoment.gloria),  # C

            MassMoment.lettura_1: [self.bible.get(MassMoment.lettura_1)],  # L
            MassMoment.salmo: [self.bible.get(MassMoment.salmo)],  # L
            MassMoment.lettura_2: [self.bible.get(MassMoment.lettura_2)],  # L
            MassMoment.alleluia: [self.bible.get(MassMoment.alleluia)],  # L
            MassMoment.vangelo: [self.bible.get(MassMoment.vangelo)],  # L

            MassMoment.credo: [Pages(body=credo_apostolico)],  # R
            MassMoment.offertorio: self.librone.get(MassMoment.offertorio),  # C

            MassMoment.padre_nostro: [Pages(body=padre_nostro)],  # R
            MassMoment.pace: self.librone.get(MassMoment.pace),  # C

            MassMoment.agnello: [Pages(body=agnello)],  # R
            MassMoment.invito_cena: [Pages(body=invito_cena)],  # R

            MassMoment.comunione: self.librone.get(MassMoment.comunione),  # C
            MassMoment.fine: self.librone.get(MassMoment.fine),  # C
        }

        self.setWindowTitle(f'Messa del {aaaammdd}')
        main_layout = QHBoxLayout()
        main_frame = QFrame()

        self.body = QLabel(f'Messa del {aaaammdd}')
        # self.body.setStyleSheet("font-size: 45pt;")
        self.body.setFont(QFont("Roboto", 50))
        self.body.setWordWrap(True)
        self.body.setContentsMargins(20, 0, 20, 0)

        main_layout.addWidget(self.body)
        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)
        self.setFocus()

        self.page_pointer = -1
        self.pages = []
        self.words_per_page = 90

    def load_songs(self, mass_moment, song):
        self.mass_structure[mass_moment].append(song)

    def paginate(self, txt):
        words = txt.split(" ")
        return [" ".join(words[i:i + self.words_per_page]) for i in range(0, len(words), self.words_per_page)]

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key.Key_Left:
                self.on_left()
            elif event.key() == Qt.Key.Key_Right:
                self.on_right()
        except Exception as e:
            print(e)

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

        self.librone = Librone("../librone.json")
        self.songs_by_moment = self.librone.load_songs_by_moment()

        main_layout = QVBoxLayout()
        main_frame = QFrame()

        load_layout = QHBoxLayout()
        self.txt_filename = QLineEdit()
        self.txt_filename.setEnabled(False)
        btn_pick_file = QPushButton('...')
        btn_pick_file.clicked.connect(self.on_pick_file)
        bnt_load_file = QPushButton('Carica Messa')
        bnt_load_file.clicked.connect(self.on_load_file)
        load_layout.addWidget(self.txt_filename)
        load_layout.addWidget(btn_pick_file)
        load_layout.addWidget(bnt_load_file)

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
            self.list_songs[mom].setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
            ly.addWidget(lbl)
            ly.addWidget(self.list_songs[mom])

            layout_songs.addLayout(ly)

        main_layout.addLayout(new_layout)
        main_layout.addLayout(layout_songs)
        main_layout.addLayout(load_layout)

        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)

    def on_pick_file(self):
        pass

    def on_load_file(self):
        pass

    def on_save_messa(self):
        songs = {}
        for moment, ls in self.list_songs.items():
            songs[moment.name] = [it.text() for it in ls.selectedItems()]

        date = self.date_edit.date().toString("yyyyMMdd")
        bible = Bible(aaaammdd=date)
        lectures = {}
        for moment, lect in bible.lectures.items():
            lectures[moment.name] = lect.to_json()

        messa_js = {
            "date": date,
            "songs": songs,
            "lectures": lectures
        }

        with open(f'../messa_{date}.json', 'w', encoding="utf-8") as outfile:
            json.dump(messa_js, outfile, indent=4)






stylesheet = {
    # Button colors
    'danger': '#dc3545',
    'warning': '#ffc107',
    'success': '#13191c',
    # Font
    'font_family': 'Roboto',
}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet("""
    #     QWidget {
    #         background-color: black;
    #         color: white;
    #     }
    # """)

    apply_stylesheet(app, theme='light_blue.xml', invert_secondary=True, extra=stylesheet)

    # create the instance of our Window
    # window = Mass(aaaammdd="20240908")
    window = Launcher()
    window.showMaximized()

    # start the app
    sys.exit(app.exec())
