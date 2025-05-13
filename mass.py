import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QFrame, QDialog, QDialogButtonBox, QVBoxLayout

from model.commons import MassMoment, Pages, NewsFetcher
from model.rfixed_rites import *
casi_duso = """

# BASE
- TASTO PER aggiungere immagine volante/predefinita, solitamente alla fine
- TASTO PER aggiungere canzone volante, poco prima della messa, ma anche durante prendendo spunto dall'omelia

# EXTRA
- canti con doppie voci
"""


class InstrDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = (
            QDialogButtonBox.StandardButton.Ok
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        message = QLabel("<b>Comandi<b><br>"
                         "ESC: esci"
                         "-&gt; Avanti<br>"
                         "&lt;- Indietro<br>"
                         "+ Zoom In<br>"
                         "- Zoom Out<br>")
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def accept(self):
        self.close()


class MassPresenter(QMainWindow):
    def __init__(self, aaaammdd, body_font_family=None, default_font_size=43):
        super().__init__()
        self.on_close = lambda: None
        self.fullscreen = True
        self.one_section_per_page = True
        self.cover = True
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
            MassMoment.silence,

            MassMoment.pace,
            MassMoment.silence,

            MassMoment.agnello,
            MassMoment.silence,

            MassMoment.invito_cena,
            MassMoment.silence,

            MassMoment.comunione,
            MassMoment.silence,

            MassMoment.news,
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
            MassMoment.credo: [Pages(body=credo_apostolico), Pages(body=credo_apostolico_2),
                               Pages(body=credo_tradizionale), Pages(body=credo_tradizionale_2),
                               Pages(body=credo_tradizionale_3), Pages(body=credo_tradizionale_4)],  # R
            MassMoment.offertorio: [],  # C
            MassMoment.santo: [],  # TODO
            MassMoment.padre_nostro: [Pages(body=padre_nostro)],  # R
            MassMoment.pace: [],  # C
            MassMoment.agnello: [Pages(body=agnello)],  # R
            MassMoment.invito_cena: [Pages(body=invito_cena)],  # R
            MassMoment.comunione: [],  # C
            MassMoment.news: [Pages(body=NewsFetcher.fetch_news())],
            MassMoment.fine: [],  # C
        }

        self.body_font_family = body_font_family
        self.default_font_size = default_font_size
        self.body_font_size = self.default_font_size
        self.body_font = QFont(self.body_font_family, self.body_font_size)

        self.setWindowTitle(f'Messa del {aaaammdd}')
        main_layout = QHBoxLayout()
        main_frame = QFrame()

        self.body = QLabel('')
        self.body.setFont(self.body_font)
        self.body.setWordWrap(True)
        self.body.setContentsMargins(20, 0, 20, 0)
        self.body.setProperty('class', 'main_label')

        self.cover_image = QLabel()
        self.cover_image.setProperty('class', 'main_label')

        main_layout.addWidget(self.body)
        main_layout.addWidget(self.cover_image, alignment=Qt.AlignmentFlag.AlignCenter)
        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)
        self.setFocus()

        self.page_pointer = -1
        self.pages = []
        self.words_per_page = 80

    def set_bible(self, bible):
        self.bible = bible
        self.mass_structure[MassMoment.lettura_1] = [self.bible.get(MassMoment.lettura_1)]  # L
        self.mass_structure[MassMoment.salmo] = [self.bible.get(MassMoment.salmo)]  # L
        self.mass_structure[MassMoment.lettura_2] = [self.bible.get(MassMoment.lettura_2)]  # L
        self.mass_structure[MassMoment.alleluia] = [self.bible.get(MassMoment.alleluia)]  # L
        self.mass_structure[MassMoment.vangelo] = [self.bible.get(MassMoment.vangelo)]  # L

        daily_header, img_available, img_filename = self.bible.get_cover_slide()
        if img_available:
            img = QPixmap(img_filename)
            img = img.scaled(img.width() * 3, img.height() * 3, Qt.AspectRatioMode.KeepAspectRatio)
            self.cover_image.setPixmap(img)
        else:
            self.cover_image.hide()

        self.body.setText(daily_header)
        self.body.setFont(QFont(self.body_font_family, self.body_font_size))
        self.cover = img_available

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
        if event.key() in [Qt.Key.Key_Plus, Qt.Key.Key_Up, Qt.Key.Key_VolumeUp]:
            self.zoom_in()
        elif event.key() in [Qt.Key.Key_Minus, Qt.Key.Key_Down, Qt.Key.Key_VolumeDown]:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in [Qt.Key.Key_Left, Qt.Key.Key_PageUp]:
            self.on_left()
        elif event.key() in [Qt.Key.Key_Right, Qt.Key.Key_PageDown]:
            self.on_right()

    def zoom_in(self):
        self.body_font_size += 2
        self.body_font.setPointSize(self.body_font_size)
        self.body.setFont(self.body_font)

    def reset_font(self):
        self.body_font_size = self.default_font_size
        self.body_font.setPointSize(self.body_font_size)
        self.body.setFont(self.body_font)

    def zoom_out(self):
        self.body_font_size -= 2
        self.body_font.setPointSize(self.body_font_size)
        self.body.setFont(self.body_font)

    def reset_page_view(self):
        self.reset_font()
        if self.fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()

        if self.cover:
            self.cover = False
            self.cover_image.hide()

    def update_pages_to_show(self, mass_el):
        if mass_el == MassMoment.silence:
            self.pages = [""]
        elif len(self.mass_structure[mass_el]) == 0:
            self.pages = [""]
        else:
            self.pages = []
            for el in self.mass_structure[mass_el]:
                for p in el.get_pages(
                        font=self.body_font,
                        max_width=self.body.width()-40, max_height=self.body.height()-40,
                        wpp=self.words_per_page,
                        one_section_per_page=self.one_section_per_page):
                    self.pages.append(p)
        self.page_pointer = 0

    def on_left(self):
        self.reset_page_view()

        self.page_pointer -= 1
        if self.page_pointer < 0:
            # Previous Section
            self.mass_moment_pointer = max(0, self.mass_moment_pointer - 1)
            mass_el = self.sequence[self.mass_moment_pointer]
            if mass_el == MassMoment.welcome:
                self.page_pointer = 0
                self.mass_moment_pointer = 1
                return

            self.update_pages_to_show(mass_el)
            self.page_pointer = len(self.pages) - 1

        self.body.setText(self.pages[self.page_pointer])

    def on_right(self):
        self.reset_page_view()

        self.page_pointer += 1
        if self.page_pointer >= len(self.pages):
            # Next Section
            self.mass_moment_pointer = min(len(self.sequence), self.mass_moment_pointer + 1)
            if self.mass_moment_pointer >= len(self.sequence):
                self.on_close()
                self.close()
                return

            mass_el = self.sequence[self.mass_moment_pointer]
            self.update_pages_to_show(mass_el)
        self.body.setText(self.pages[self.page_pointer])

    def add(self, mass_moment, song):
        self.mass_structure[mass_moment].append(song)

    def run(self, fullscreen=True, one_section_per_page=False, on_close=lambda: None):
        dlg = InstrDialog()
        self.on_close = on_close
        self.fullscreen = fullscreen
        self.one_section_per_page=one_section_per_page
        if self.fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()
        dlg.exec()
