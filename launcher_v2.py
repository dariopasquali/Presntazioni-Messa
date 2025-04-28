import json
import os
import sys
from functools import partial

import requests
from PyQt6.QtCore import QDate, QThread, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, \
    QDateEdit, QPushButton, QLineEdit, QFrame, QMainWindow, QDialog, QDialogButtonBox, QMenuBar, QToolBar, QTextEdit, \
    QCheckBox, QGroupBox
from qt_material import apply_stylesheet

from model.bible import Bible
from model.librone import Librone
from mass import MassPresenter
from model.commons import MassMoment

import subprocess

from update_manager import UpdateManager

import logging


class SongPieceListItem(QListWidgetItem):
    def __init__(self, text="", rit_key=None, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.rit_key = rit_key

    def get_text(self):
        if self.rit_key is not None:
            return self.rit_key

        return self.text()


class SongListItem(QListWidgetItem):
    def __init__(self, song=None, *args, **kwargs):
        super().__init__(song.title, *args, **kwargs)
        self.song = song

    def get_pages(self):
        return self.song.get_pages()


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

        self.check_intro = QCheckBox("intro")
        self.check_gloria = QCheckBox("gloria")
        self.check_offertorio = QCheckBox("offertorio")
        self.check_santo = QCheckBox("santo")
        self.check_pace = QCheckBox("pace")
        self.check_comunione = QCheckBox("comunione")
        self.check_fine = QCheckBox("fine")

        ly_moments = QHBoxLayout()
        self.moments_check_list = {
            "intro": self.check_intro,
            "gloria": self.check_gloria,
            "offertorio": self.check_offertorio,
            "santo": self.check_santo,
            "pace": self.check_pace,
            "comunione": self.check_comunione,
            "fine": self.check_fine
        }

        for name, check in self.moments_check_list.items():
            ly_moments.addWidget(check)

        head_layout = QHBoxLayout()
        head_layout.addWidget(self.txt_title)
        head_layout.addWidget(self.txt_number)

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
        left_layout.addLayout(ly_moments)
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

        self.logger = logging.getLogger(__name__)
        self.logger.info("Window build done")

    def add_strofa(self):
        txt = self.txt_strofa.toPlainText()
        if txt == "":
            return
        self.song.addItem(SongPieceListItem(txt))
        self.song_list.append(txt)
        self.txt_strofa.clear()

    def add_ritornello(self, lbl):
        txt = self.rit_map.get(lbl, "").toPlainText()
        if txt == "":
            return
        self.song.addItem(SongPieceListItem(text=txt, rit_key=lbl))
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
        for name, check in self.moments_check_list.items():
            check.setChecked(False)
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
            moments = [name for name, check in self.moments_check_list.items() if check.isChecked()]

            self.add_song_callback(title, number, moments, rits, structure)

        self.reset()
        super().accept()

    def reject(self):
        self.reset()
        super().reject()


class ManageLibrone(QDialog):
    def __init__(self, delete_song_callback, add_song_callback):
        super().__init__()
        self.setWindowTitle("Gestione Librone")
        self.setGeometry(0, 0, 700, 700)

        self.ext_delete_song_callback = delete_song_callback
        self.ext_add_song_callback = add_song_callback
        self.librone = None

        self.add_song_dialog = AddSongDialog(self.ext_add_song_callback)

        btn_add = QPushButton("Aggiungi")
        btn_add.clicked.connect(self.add_song)

        btn_edit = QPushButton("Modifica")
        btn_edit.clicked.connect(self.edit_song)

        btn_remove = QPushButton("Elimina")
        btn_remove.clicked.connect(self.remove_song)

        ly_btn = QHBoxLayout()
        ly_btn.addWidget(btn_add)
        ly_btn.addWidget(btn_edit)
        ly_btn.addWidget(btn_remove)

        self.songs_list = QListWidget()
        self.songs_list.itemClicked.connect(self.show_lyrics)
        self.txt_song = QTextEdit("")
        self.txt_song.setStyleSheet("color: white")

        ly_songs = QHBoxLayout()
        ly_songs.addWidget(self.songs_list)
        ly_songs.addWidget(self.txt_song)

        layout = QVBoxLayout()
        layout.addLayout(ly_btn)
        layout.addLayout(ly_songs)

        self.setLayout(layout)

    def add_song(self):
        self.add_song_dialog.show()

    def edit_song(self):
        pass

    def remove_song(self):
        title = self.songs_list.currentItem().text()
        self.ext_delete_song_callback(title=title)

    def set_librone(self, librone):
        self.librone = librone
        self.load_songs()

    def load_songs(self):
        self.txt_song.clear()
        self.songs_list.clear()
        for s in self.librone:
            self.songs_list.addItem(SongListItem(song=s, ))

    def show_lyrics(self, item):
        pages = item.get_pages()
        html_txt = ""
        for page in pages:
            html_txt += f"{page}<br>"
        self.txt_song.setText(html_txt)


class UpdateDialog(QDialog):
    def __init__(self, update_worker):
        super().__init__()
        self.new_version = 0.0

        self.lbl = QLabel("Trovata nuova versione, Aggiornare?")
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        ly = QVBoxLayout()
        ly.addWidget(self.lbl)
        ly.addWidget(button_box)
        self.setLayout(ly)

        self.thread = QThread()
        self.update_worker = update_worker

    def accept(self):
        self.update_worker.moveToThread(self.thread)
        self.thread.started.connect(self.update_worker.update)
        self.thread.start()


class LauncherV2(QMainWindow):
    def __init__(self, file_librone="librone.json"):
        super().__init__()

        self.messa = None
        self.date = ""
        self.bible = Bible()
        self.librone = Librone("librone.json")
        self.songs = []
        self.songs_lists = []

        # MAIN LAYOUT =================================================

        main_layout = QHBoxLayout()
        main_frame = QFrame()

        ly_left = QVBoxLayout()

        check_intro = QCheckBox("Ingresso")
        check_intro.setStyleSheet("font-size: 12pt")
        check_intro.stateChanged.connect(self.on_check_moment_change)
        check_gloria = QCheckBox("Gloria")
        check_gloria.setStyleSheet("font-size: 12pt")
        check_gloria.stateChanged.connect(self.on_check_moment_change)
        check_offertorio = QCheckBox("Offertorio")
        check_offertorio.setStyleSheet("font-size: 12pt")
        check_offertorio.stateChanged.connect(self.on_check_moment_change)
        check_pace = QCheckBox("Pace")
        check_pace.setStyleSheet("font-size: 12pt")
        check_pace.stateChanged.connect(self.on_check_moment_change)
        check_comunione = QCheckBox("Comunione")
        check_comunione.setStyleSheet("font-size: 12pt")
        check_comunione.stateChanged.connect(self.on_check_moment_change)
        check_fine = QCheckBox("Fine")
        check_fine.setStyleSheet("font-size: 12pt")
        check_fine.stateChanged.connect(self.on_check_moment_change)

        self.moments_checkboxes = {
            MassMoment.intro: check_intro,
            MassMoment.gloria: check_gloria,
            MassMoment.offertorio: check_offertorio,
            MassMoment.pace: check_pace,
            MassMoment.comunione: check_comunione,
            MassMoment.fine: check_fine
        }

        group_moments = QGroupBox("Momenti Messa")
        ly_moments = QHBoxLayout()
        ly_moments.addWidget(check_intro)
        ly_moments.addWidget(check_gloria)
        ly_moments.addWidget(check_offertorio)
        ly_moments.addWidget(check_pace)
        ly_moments.addWidget(check_comunione)
        ly_moments.addWidget(check_fine)
        group_moments.setLayout(ly_moments)

        ly_left.addWidget(group_moments)

        self.songs_list = QListWidget()
        self.songs_list.setStyleSheet("font-size: 12pt")
        self.songs_list.itemClicked.connect(self.show_lyrics)
        self.txt_song = QTextEdit("")
        self.txt_song.setStyleSheet("color: white; font-size: 18pt")

        ly_songs = QHBoxLayout()
        ly_songs.addWidget(self.songs_list)
        ly_songs.addWidget(self.txt_song)
        self.load_songs()

        ly_left.addLayout(ly_songs)

        # ==========TOOLBAR====================
        toolbar = QToolBar("Tools")
        self.addToolBar(toolbar)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("color: rgb(255, 255, 255);")
        self.date_edit.dateChanged.connect(self.on_date_select)
        toolbar.addWidget(self.date_edit)

        self.act_start = QAction(QIcon("start.png"), 'INIZIA MESSA!', self)
        self.act_start.triggered.connect(self.on_start_messa)
        toolbar.addAction(self.act_start)

        # ======= MENU =========================================

        menu = self.menuBar()

        act_add_song = QAction("Gestisci Canzoni", self)
        act_add_song.triggered.connect(self.manage_songs)

        act_sync_librone = QAction("Scarica Librone", self)
        act_sync_librone.triggered.connect(self.sync_librone)

        act_upload_librone = QAction("Carica Librone Aggiornato", self)
        act_upload_librone.triggered.connect(self.upload_librone)

        act_check_update = QAction("Verifica Aggiornamenti", self)
        act_check_update.triggered.connect(self.check_for_updates)

        menu_librone = menu.addMenu("Librone")
        menu_librone.addAction(act_add_song)
        menu_librone.addAction(act_sync_librone)
        menu_librone.addAction(act_upload_librone)

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

        main_layout.addLayout(ly_left)

        main_frame.setLayout(main_layout)
        self.setCentralWidget(main_frame)

        self.manage_songs_dialog = ManageLibrone(
            delete_song_callback=self.delete_song_callback,
            add_song_callback=self.add_song_callback
        )

        self.update_manager = UpdateManager()
        self.update_dialog = UpdateDialog(self.update_manager)

        self.webapp_mass = []
        self.fetch_saved_mass_from_webapp()

    def on_check_moment_change(self, checked):
        selected_moments = [k for (k, check_box) in self.moments_checkboxes.items() if check_box.isChecked()]

        self.songs_list.clear()
        if not selected_moments:
            songs_sublist = self.songs
        else:
            songs_sublist = [s for s in self.songs if any(tag for tag in s.tags if tag in selected_moments)]

        for song in songs_sublist:
            self.songs_list.addItem(SongListItem(song=song, ))

    def load_songs(self):
        self.txt_song.clear()
        self.songs_list.clear()

        self.songs = self.librone.get_all_songs()
        for song in self.songs:
            self.songs_list.addItem(SongListItem(song=song, ))

    def show_lyrics(self, item):
        pages = item.get_pages()
        html_txt = ""
        for page in pages:
            html_txt += f"{page}<br>"
        self.txt_song.setText(html_txt)

    def fetch_saved_mass_from_webapp(self):
        response = requests.get("https://corogiovani.pythonanywhere.com/messa/list")
        self.webapp_mass = response.json()
        self.on_date_select()

    def load_webapp_mass(self, date):
        pass
        # if date in self.webapp_mass:
        #     response = requests.get(f"https://corogiovani.pythonanywhere.com/messa/{date}")
        #     songs = response.json()
        #
        #     scaletta = {}
        #     for moment_name, song_list in songs.items():
        #         moment = MassMoment.from_name(moment_name)
        #         scaletta[moment] = song_list
        #         for id in range(self.list_songs[moment].count()):
        #             item = self.list_songs[moment].item(id)
        #             for s in song_list:
        #                 if s == item.text():
        #                     item.setSelected(True)
        #
        #     self.librone.load_songs(scaletta)
        # else:
        #     for moment_name in self.lbl_canto_text.keys():
        #         if moment_name in self.list_songs:
        #             self.list_songs[moment_name].clearSelection()

    def on_date_select(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        self.load_webapp_mass(date)

    def manage_songs(self):
        self.manage_songs_dialog.set_librone(self.librone.get_all_songs())
        self.manage_songs_dialog.show()

    def delete_song_callback(self, title):
        ok = self.librone.delete_song(title)
        if ok:
            self.populate_song_lists(reload=True)
            self.manage_songs_dialog.set_librone(self.librone.get_all_songs())

    def add_song_callback(self, title, number, moments, rits, structure):
        ok = self.librone.add_song(
            title=title,
            number=number,
            moments=moments,
            rits=rits,
            structure=structure
        )

        if ok:
            self.populate_song_lists(reload=True)
            self.manage_songs_dialog.set_librone(self.librone.get_all_songs())

    def sync_librone(self):
        if self.librone.check_for_updates():
            self.populate_song_lists(reload=True)
            self.manage_songs_dialog.set_librone(self.librone.scaletta)

    def upload_librone(self):
        self.librone.upload_new_version()

    def check_for_updates(self):
        new_version, v = self.update_manager.check_for_updates()
        if new_version:
            self.update_dialog.show()

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]
                        )

    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_lightgreen.xml', invert_secondary=False,
                     extra=stylesheet, css_file="custom.css")

    # create the instance of our Window
    # window = Mass(aaaammdd="20240908")
    window = LauncherV2()
    window.showMaximized()

    # start the app
    sys.exit(app.exec())
