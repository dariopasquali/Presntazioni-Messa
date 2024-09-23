import json
import os
import sys
from functools import partial

from PyQt6 import QtCore
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, \
    QDateEdit, QPushButton, QLineEdit, QFrame, QMainWindow, QDialog, QDialogButtonBox, QMenuBar, QToolBar, QTextEdit
from qt_material import apply_stylesheet

from model.bible import Bible
from model.librone import Librone
from mass import MassPresenter
from model.commons import MassMoment

import subprocess


class SongListElement(QListWidgetItem):
    def __init__(self, text="", rit_key=None, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.rit_key = rit_key

    def get_text(self):
        if self.rit_key is not None:
            return self.rit_key

        return self.text()


class AddSongDialog(QDialog):
    def __init__(self, add_song_callback):
        super().__init__()
        self.add_song_callback = add_song_callback

        self.rit_counter = 0
        self.rit_map = {}
        self.rit_callback_map = {}
        self.song_list = []

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)  # Vertical line
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)  # Vertical line
        separator2.setFrameShadow(QFrame.Shadow.Sunken)

        self.setWindowTitle("Aggiungi Canzone")
        layout = QVBoxLayout()

        self.txt_title = QTextEdit()
        self.txt_title.setPlaceholderText("Titolo")

        self.txt_number = QTextEdit()
        self.txt_number.setPlaceholderText("Numero Librone")

        self.txt_momento = QTextEdit()
        self.txt_momento.setPlaceholderText("Inserisci i momenti della messa in cui può essere usato il canto "
                                            "separati da spazio.\nPossibili valori: intro, gloria, offertorio, santo,"
                                            " pace, comunione, fine.")
        self.txt_momento.setToolTip("Inserisci i momenti della messa in cui può essere usato il canto separati da "
                                    "spazio.\nPossibili valori: intro, gloria, offertorio, santo, pace, comunione, "
                                    "fine.")

        head_layout = QHBoxLayout()
        head_layout.addWidget(self.txt_title)
        head_layout.addWidget(self.txt_number)
        head_layout.addWidget(self.txt_momento)

        self.ly_rits = QVBoxLayout()
        self.btn_add_rit = QPushButton("Aggiungi Ritornello")
        self.btn_add_rit.clicked.connect(self.new_rit)
        self.ly_rits.addWidget(self.btn_add_rit)
        self.new_rit()

        self.txt_strofa = QTextEdit()
        self.txt_strofa.setPlaceholderText("Strofa")
        btn_add_strofa = QPushButton("Aggiungi")
        btn_add_strofa.clicked.connect(self.add_strofa)
        ly_strofa = QHBoxLayout()
        ly_strofa.addWidget(self.txt_strofa)
        ly_strofa.addWidget(btn_add_strofa)

        left_layout = QVBoxLayout()
        left_layout.addLayout(head_layout)
        left_layout.addWidget(separator)
        left_layout.addLayout(self.ly_rits)
        left_layout.addWidget(separator2)
        left_layout.addLayout(ly_strofa)

        self.song = QListWidget()
        self.song.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        body_layout = QHBoxLayout()
        body_layout.addLayout(left_layout)
        body_layout.addWidget(self.song)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(body_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_strofa(self):
        txt = self.txt_strofa.toPlainText()
        if txt == "":
            return
        self.song.addItem(SongListElement(txt))
        self.song_list.append(txt)
        self.txt_strofa.clear()

    def add_ritornello(self, lbl):
        txt = self.rit_map.get(lbl, "").toPlainText()
        if txt == "":
            return
        self.song.addItem(SongListElement(text=txt, rit_key=lbl))
        self.song_list.append(lbl)

    def new_rit(self):
        lbl = "<RIT"
        if self.rit_counter == 0:
            lbl += ">"
        else:
            lbl += f"{self.rit_counter}>"

        text_box = QTextEdit()
        text_box.setPlaceholderText("Ritornello")

        self.rit_map[lbl] = text_box
        self.rit_counter += 1

        btn = QPushButton("Aggiungi")
        btn.clicked.connect(partial(self.add_ritornello, lbl))

        ly = QHBoxLayout()
        ly.addWidget(QLabel(lbl))
        ly.addWidget(text_box)
        ly.addWidget(btn)
        self.ly_rits.addLayout(ly)

    def remove_items(self, layout):
        # Remove all widgets and nested layouts from the layout
        while layout.count():
            item = layout.itemAt(0)
            if item.widget():  # If the item is a widget
                item.widget().deleteLater()
            elif item.layout():  # If the item is a layout
                self.remove_items(item.layout())  # Recursively remove items from the nested layout
            layout.removeItem(item)  # Remove the item from the layout

    def reset(self):
        self.rit_map.clear()
        self.rit_counter = 0
        self.song_list.clear()
        self.song.clear()
        self.txt_strofa.clear()
        self.txt_number.clear()
        self.txt_momento.clear()
        self.txt_title.clear()
        self.remove_items(self.ly_rits)
        self.btn_add_rit = QPushButton("Aggiungi Ritornello")
        self.btn_add_rit.clicked.connect(self.new_rit)
        self.ly_rits.addWidget(self.btn_add_rit)
        self.new_rit()

    def accept(self):
        title = self.txt_title.toPlainText()

        rits = {(lbl, text.toPlainText()) for (lbl, text) in self.rit_map.items()}
        structure = [self.song.item(i).get_text() for i in range(self.song.count())]

        if title != "":
            number = self.txt_number.toPlainText()
            momento = self.txt_momento.toPlainText()
            self.add_song_callback(title, number, momento, rits, structure)

        self.reset()
        super().accept()

    def reject(self):
        self.reset()
        super().reject()


class Launcher(QMainWindow):
    def __init__(self, file_librone="librone.json"):
        super().__init__()

        self.messa = None
        self.date = ""
        self.bible = Bible()
        self.librone = Librone("librone.json")
        self.songs_by_moment = {}

        main_layout = QVBoxLayout()
        main_frame = QFrame()

        new_layout = QHBoxLayout()

        # ==========TOOLBAR====================
        toolbar = QToolBar("Tools")
        self.addToolBar(toolbar)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("color: rgb(255, 255, 255);")
        toolbar.addWidget(self.date_edit)

        act_save = QAction('Salva PDF Messa', self)
        act_save.triggered.connect(self.on_save_messa)
        toolbar.addAction(act_save)

        act_pick = QAction('Carica Messa', self)
        act_pick.triggered.connect(self.on_pick_file)
        toolbar.addAction(act_pick)

        toolbar.addSeparator()

        self.act_start = QAction(QIcon("start.png"), 'INIZIA MESSA!', self)
        self.act_start.triggered.connect(self.on_start_messa)
        toolbar.addAction(self.act_start)

        # ======= MENU =========================================

        menu = self.menuBar()

        act_add_song = QAction("Aggiungi Canzone", self)
        act_add_song.triggered.connect(self.add_song)

        act_sync_librone = QAction("Sincronizza con Google Drive", self)
        act_sync_librone.triggered.connect(self.sync_librone)

        act_check_update = QAction("Verifica Aggiornamenti", self)
        act_check_update.triggered.connect(self.check_for_updates)

        menu_librone = menu.addMenu("Librone")
        menu_librone.addAction(act_add_song)
        menu_librone.addAction(act_sync_librone)

        menu_software = menu.addMenu("Aggiorna")
        menu_software.addAction(act_check_update)

        self.lbl_canto_text = {
            MassMoment.intro: "Ingresso",
            MassMoment.gloria: "Gloria",
            MassMoment.offertorio: "Offertorio",
            MassMoment.santo: "Santo",
            MassMoment.pace: "Pace",
            MassMoment.comunione: "Comunione",
            MassMoment.fine: "Uscita"
        }

        self.list_songs = {}
        self.layout_songs = QHBoxLayout()
        self.populate_song_lists()

        main_layout.addLayout(new_layout)
        main_layout.addLayout(self.layout_songs)

        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)

        self.add_song_dialog = AddSongDialog(self.add_song_callback)

    def add_song(self):
        self.add_song_dialog.show()

    def add_song_callback(self, title, number, moments_txt, rits, structure):
        moments = moments_txt.split(" ")
        ok = self.librone.add_song(
            title=title,
            number=number,
            moments=moments,
            rits=rits,
            structure=structure
        )

        if ok:
            self.populate_song_lists(reload=True)

    def sync_librone(self):
        if self.librone.check_for_updates():
            self.populate_song_lists(reload=True)

    def check_for_updates(self):
        pass

    def populate_song_lists(self, reload=False):
        self.songs_by_moment = self.librone.load_songs_by_moment()
        for mom, head in self.lbl_canto_text.items():
            ly = QVBoxLayout()
            lbl = QLabel(f"<b>{head}:</b>")
            if reload:
                self.list_songs[mom].clear()
            else:
                self.list_songs[mom] = QListWidget()

            for title in sorted(self.songs_by_moment[mom]):
                self.list_songs[mom].addItem(QListWidgetItem(title))
            self.list_songs[mom].setSelectionMode(QListWidget.SelectionMode.MultiSelection)

            if not reload:
                ly.addWidget(lbl)
                ly.addWidget(self.list_songs[mom])
                self.layout_songs.addLayout(ly)

    def on_start_messa(self):
        # Set and configure the messa
        self.get_data()
        self.messa = MassPresenter(aaaammdd=self.date)
        self.messa.set_bible(self.bible)
        self.messa.set_librone(self.librone)
        self.messa.run_fullscreen()

    def on_pick_file(self):
        os.makedirs("messe", exist_ok=True)
        fname = QFileDialog.getOpenFileName(self, 'Open file', 'messe')[0]

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
        self.messa.run_fullscreen(pdf_filename=f'messe/messa_{self.date}.pdf', on_close=self.on_close)

    def on_close(self):
        subprocess.call("explorer messe", shell=True)


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
