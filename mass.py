import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QFrame, QDialog, QDialogButtonBox, QVBoxLayout

from model.commons import MassMoment, Pages
from model.rfixed_rites import *
from pdf import PDFMaker

casi_duso = """

# BASE
- Eseguibile

- Download dicitura tempo ordinario e messa + data
- Paginazione più smart, canti (strofa + RIT in pagina), letture (wpp 150), fixed (wpp 100)

- TASTO PER aggiungere immagine volante/predefinita, solitamente alla fine
- TASTO PER aggiungere canzone volante, poco prima della messa, ma anche durante prendendo spunto dall'omelia

- librone su drive, scaricare canzoni in fase di creazione nel file .json

# EXTRA
- canti con doppie voci
- sequenze particolari (sequenza pasquale,)
"""


class InstrDialog(QDialog):
    def __init__(self, pdf_maker_mode=False):
        super().__init__()

        self.setWindowTitle("HELLO!")

        QBtn = (
            QDialogButtonBox.StandardButton.Ok
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        if not pdf_maker_mode:
            message = QLabel("<b>Comandi<b><br>"
                             "ESC: esci"
                             "-&gt; Avanti<br>"
                             "&lt;- Indietro<br>"
                             "+ Zoom In<br>"
                             "- Zoom Out<br>")
        else:
            message = QLabel("<b>Aggiusta la dimensione del testo con i tasti + e -<b><br>"
                             "<b>Quindi premi <b>Freccia Destra -&gt;</b> per aggiungere la Slide al PDF<b><br>"
                             "+ Zoom In<br>"
                             "- Zoom Out<br>"
                             "ESC: esci")
        # message.setStyleSheet("font-size: 30pt")
        layout.addWidget(message)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def accept(self):
        self.close()


class MassPresenter(QMainWindow):
    def __init__(self, aaaammdd, pdf_maker_mode=False):
        super().__init__()
        self.on_close = lambda: None
        self.pdf_maker_mode = pdf_maker_mode
        self.pdf_maker = PDFMaker()

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
            MassMoment.santo: [],  # TODO
            MassMoment.padre_nostro: [Pages(body=padre_nostro)],  # R
            MassMoment.pace: [],  # C
            MassMoment.agnello: [Pages(body=agnello)],  # R
            MassMoment.invito_cena: [Pages(body=invito_cena)],  # R
            MassMoment.comunione: [],  # C
            MassMoment.fine: [],  # C
        }

        self.default_font = 40
        self.body_font = self.default_font

        self.setWindowTitle(f'Messa del {aaaammdd}')
        main_layout = QHBoxLayout()
        main_frame = QFrame()

        self.body = QLabel(f'Messa del {aaaammdd}')
        self.body.setStyleSheet(f"font-size: {self.body_font}pt;")
        # self.body.setFont(QFont("Roboto", 50))
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
        if event.key() == Qt.Key.Key_Plus:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in [Qt.Key.Key_Left, Qt.Key.Key_PageUp]:
            if not self.pdf_maker_mode:
                self.on_left()
        elif event.key() in [Qt.Key.Key_Right, Qt.Key.Key_PageDown]:
            self.on_right()

    def zoom_in(self):
        self.body_font += 2
        self.body.setStyleSheet(f"font-size: {self.body_font}pt;")

    def reset_font(self):
        self.body_font = self.default_font
        self.body.setStyleSheet(f"font-size: {self.body_font}pt;")

    def zoom_out(self):
        self.body_font -= 2
        self.body.setStyleSheet(f"font-size: {self.body_font}pt;")

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

    def on_right(self):
        # Store the last page
        self.showFullScreen()
        if self.pdf_maker_mode and self.page_pointer >= 0:
            self.pdf_maker.new_page(self.pages[self.page_pointer], font_size=self.body_font)
            self.reset_font()

        self.page_pointer += 1
        if self.page_pointer >= len(self.pages):
            # Next Section
            self.mass_moment_pointer = min(len(self.sequence), self.mass_moment_pointer + 1)
            if self.mass_moment_pointer >= len(self.sequence):
                if self.pdf_maker_mode:
                    self.pdf_maker.write_pdf()
                self.on_close()
                self.close()
                return

            mass_el = self.sequence[self.mass_moment_pointer]

            if mass_el == MassMoment.silence:
                self.pages = [""]
            elif len(self.mass_structure[mass_el]) == 0:
                self.pages = [""]
            else:
                self.pages = []
                for el in self.mass_structure[mass_el]:
                    for p in el.get_pages(wpp=self.words_per_page):
                        self.pages.append(p)
            self.page_pointer = 0

        try:
            self.body.setText(self.pages[self.page_pointer])
        except Exception as e:
            print(e)

    def add(self, mass_moment, song):
        self.mass_structure[mass_moment].append(song)

    def run_fullscreen(self, pdf_filename="messa.pdf", on_close=lambda: None):
        dlg = InstrDialog(pdf_maker_mode=self.pdf_maker_mode)
        self.pdf_maker.set_filename(pdf_filename)
        self.on_close = on_close
        self.showFullScreen()
        dlg.exec()
        # dlg.show()

    def run_maximized(self, pdf_filename="messa/messa.pdf", on_close=lambda: None):
        dlg = InstrDialog(pdf_maker_mode=self.pdf_maker_mode)
        self.pdf_maker.set_filename(pdf_filename)
        self.on_close = on_close
        self.showMaximized()
        dlg.exec()
        # dlg.show()
