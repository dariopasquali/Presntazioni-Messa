import json
import os
import sys

from PyQt6 import QtCore
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, \
    QDateEdit, QPushButton, QLineEdit, QFrame, QMainWindow
from qt_material import apply_stylesheet

from model.bible import Bible
from model.librone import Librone
from mass import MassPresenter
from model.commons import MassMoment


class Launcher(QMainWindow):
    def __init__(self, file_librone="librone.json"):
        super().__init__()

        self.messa = None
        self.date = ""
        self.bible = Bible()
        self.librone = Librone("librone.json")
        self.songs_by_moment = self.librone.load_songs_by_moment()

        main_layout = QVBoxLayout()
        main_frame = QFrame()

        load_layout = QHBoxLayout()
        self.txt_filename = QLineEdit()
        self.txt_filename.setEnabled(False)
        btn_pick_file = QPushButton('CARICA MESSA')
        btn_pick_file.clicked.connect(self.on_pick_file)
        self.btn_start = QPushButton(' INIZIA MESSA!')
        self.btn_start.setIcon(QIcon("../start.png"))
        self.btn_start.clicked.connect(self.on_start_messa)
        # self.btn_start.setEnabled(False)
        load_layout.addWidget(self.txt_filename)
        load_layout.addWidget(btn_pick_file)
        load_layout.addWidget(self.btn_start)

        new_layout = QHBoxLayout()
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("color: rgb(255, 255, 255);")
        btn_save = QPushButton('CREA PDF MESSA')
        btn_save.clicked.connect(self.on_save_messa)
        new_layout.addWidget(self.date_edit)
        new_layout.addWidget(btn_save)

        lbl_canto_text = {
            MassMoment.intro: "Ingresso",
            MassMoment.gloria: "Gloria",
            MassMoment.offertorio: "Offertorio",
            MassMoment.santo: "Santo",
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
            for title in sorted(self.songs_by_moment[mom]):
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
        self.get_data()
        self.messa = MassPresenter(aaaammdd=self.date)
        self.messa.set_bible(self.bible)
        self.messa.set_librone(self.librone)
        self.messa.run_maximized()

    def on_pick_file(self):
        os.makedirs("messe", exist_ok=True)
        fname = QFileDialog.getOpenFileName(self, 'Open file', 'messe')[0]
        self.txt_filename.setText(fname)

        if fname == "":
            return

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
            moment = MassMoment.from_name(moment_name)
            scaletta[moment] = song_list
            for id in range(self.list_songs[moment].count()):
                item = self.list_songs[moment].item(id)
                for s in song_list:
                    if s == item.text():
                        item.setSelected(True)

        self.librone.load_songs(scaletta)

        self.btn_start.setEnabled(True)

    def get_data(self):
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

        return songs, lectures

    def on_save_messa(self):

        songs, lectures = self.get_data()
        messa_js = {
            "date": self.date,
            "songs": songs,
            "lectures": lectures
        }
        os.makedirs("messe", exist_ok=True)
        with open(f'messe/messa_{self.date}.json', 'w', encoding="utf-8") as outfile:
            json.dump(messa_js, outfile, indent=4)

        self.messa = MassPresenter(aaaammdd=self.date, pdf_maker_mode=True)
        self.messa.set_bible(self.bible)
        self.messa.set_librone(self.librone)
        self.messa.run_maximized(pdf_filename=f'messe/messa_{self.date}.pdf')



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