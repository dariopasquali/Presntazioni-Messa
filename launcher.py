import json
import os
import sys
from functools import partial

import requests
from PyQt6.QtCore import QDate, QThread, QObject, Qt, pyqtSignal, QSize, QPoint, QRect, QMimeData
from PyQt6.QtGui import QIcon, QAction, QFontDatabase, QFont
from PyQt6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, \
    QDateEdit, QPushButton, QLineEdit, QFrame, QMainWindow, QDialog, QDialogButtonBox, QMenuBar, QToolBar, QTextEdit, \
    QCheckBox, QSpinBox, QGroupBox, QScrollArea, QSplitter, QAbstractItemView, QSizePolicy, QWidget, QLayout
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
    def __init__(self, add_song_callback, song=None, update_song_callback=None):
        super().__init__()
        self.add_song_callback = add_song_callback
        self.update_song_callback = update_song_callback
        self.editing_song = song
        self.original_title = song.title if song is not None else None

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

        self.setObjectName("songEditorDialog")
        self.setWindowTitle("Modifica Canzone" if song is not None else "Aggiungi Canzone")
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

        self.lbl_piece_editor = QLabel("Nuova strofa")
        self.txt_strofa = QTextEdit()
        self.txt_strofa.setPlaceholderText("Strofa")
        btn_add_strofa = QPushButton("Aggiungi")
        btn_add_strofa.clicked.connect(self.add_strofa)
        self.btn_update_piece = QPushButton("Aggiorna elemento selezionato")
        self.btn_update_piece.setEnabled(False)
        self.btn_update_piece.clicked.connect(self.update_selected_piece)
        self.btn_clear_piece = QPushButton("Deseleziona")
        self.btn_clear_piece.clicked.connect(self.clear_piece_selection)
        piece_buttons = QVBoxLayout()
        piece_buttons.addWidget(btn_add_strofa)
        piece_buttons.addWidget(self.btn_update_piece)
        piece_buttons.addWidget(self.btn_clear_piece)
        ly_strofa = QHBoxLayout()
        ly_strofa.addWidget(self.txt_strofa)
        ly_strofa.addLayout(piece_buttons)

        left_layout = QVBoxLayout()
        left_layout.addLayout(head_layout)
        left_layout.addLayout(ly_moments)
        left_layout.addWidget(separator)
        left_layout.addLayout(self.ly_rits)
        left_layout.addWidget(separator2)
        left_layout.addWidget(self.lbl_piece_editor)
        left_layout.addLayout(ly_strofa)

        self.song = QListWidget()
        self.song.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.song.currentItemChanged.connect(self.load_selected_piece)

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
        if song is not None:
            self.load_song(song)

    def load_song(self, song):
        self.txt_title.setPlainText(song.title)
        self.txt_number.setPlainText(str(song.number))
        for moment in song.tags:
            checkbox = self.moments_check_list.get(moment.name)
            if checkbox is not None:
                checkbox.setChecked(True)
        # Replace the default refrain editor with the song's real refrain fields.
        self.remove_items(self.ly_rits)
        self.rit_map.clear()
        refrain_keys = [key for key in song.raw if key.startswith("<RIT")]
        for key in sorted(refrain_keys):
            editor = QTextEdit(); editor.setPlaceholderText("Ritornello"); editor.setPlainText(song.raw[key])
            self.rit_map[key] = editor
            row = QHBoxLayout(); row.addWidget(QLabel(key)); row.addWidget(editor)
            self.ly_rits.addLayout(row)
        self.btn_add_rit = QPushButton("Aggiungi Ritornello")
        self.btn_add_rit.clicked.connect(self.new_rit)
        self.ly_rits.addWidget(self.btn_add_rit)
        self.rit_counter = len(refrain_keys)
        for element in song.body:
            self.song.addItem(SongPieceListItem(text=element, rit_key=element if element in self.rit_map else None))
            self.song_list.append(element)

    def load_selected_piece(self, item, previous=None):
        if item is None:
            self.lbl_piece_editor.setText("Nuova strofa")
            self.txt_strofa.clear()
            self.txt_strofa.setPlaceholderText("Strofa")
            self.btn_update_piece.setEnabled(False)
            return
        if item.rit_key is not None:
            self.lbl_piece_editor.setText(f"Modifica ritornello {item.rit_key}")
            editor = self.rit_map.get(item.rit_key)
            text = editor.toPlainText() if editor is not None else item.text()
            self.txt_strofa.setPlaceholderText("Testo del ritornello")
        else:
            self.lbl_piece_editor.setText("Modifica strofa")
            text = item.text()
            self.txt_strofa.setPlaceholderText("Testo della strofa")
        self.txt_strofa.setPlainText(text)
        self.btn_update_piece.setEnabled(True)

    def update_selected_piece(self):
        item = self.song.currentItem()
        if item is None:
            return
        text = self.txt_strofa.toPlainText().strip()
        if not text:
            return
        if item.rit_key is not None:
            editor = self.rit_map.get(item.rit_key)
            if editor is not None:
                editor.setPlainText(text)
            item.setText(text)
        else:
            item.setText(text)
        self.txt_strofa.setPlainText(text)

    def clear_piece_selection(self):
        self.song.clearSelection()
        self.song.setCurrentItem(None)
        self.load_selected_piece(None)

    def add_strofa(self):
        txt = self.txt_strofa.toPlainText()
        if txt == "":
            return
        self.song.addItem(SongPieceListItem(txt))
        self.song_list.append(txt)
        self.clear_piece_selection()

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
        self.lbl_piece_editor.setText("Nuova strofa")
        self.btn_update_piece.setEnabled(False)
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

            if self.editing_song is not None and self.update_song_callback is not None:
                self.update_song_callback(self.original_title, title, number, moments, rits, structure)
            else:
                self.add_song_callback(title, number, moments, rits, structure)

        self.reset()
        super().accept()

    def reject(self):
        self.reset()
        super().reject()


class ManageLibrone(QDialog):
    def __init__(self, delete_song_callback, add_song_callback, update_song_callback):
        super().__init__()
        self.setObjectName("manageLibroneDialog")
        self.setWindowTitle("Gestione Librone")
        self.setGeometry(0, 0, 700, 700)

        self.ext_delete_song_callback = delete_song_callback
        self.ext_add_song_callback = add_song_callback
        self.ext_update_song_callback = update_song_callback
        self.librone = None

        self.add_song_dialog = AddSongDialog(self.ext_add_song_callback)
        self.edit_song_dialog = None

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
        self.txt_song.setReadOnly(True)
        self.txt_song.setStyleSheet("font-size: 14pt; padding: 10px;")

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
        item = self.songs_list.currentItem()
        if item is None:
            return
        # Keep the editor as an independent top-level window, exactly like the
        # Add Song editor. Retain a reference so Qt does not garbage-collect it.
        if getattr(self, "edit_song_dialog", None) is not None:
            self.edit_song_dialog.close()
        self.edit_song_dialog = AddSongDialog(
            self.ext_add_song_callback,
            item.song,
            self.ext_update_song_callback
        )
        self.edit_song_dialog.setWindowFlag(Qt.WindowType.Window, True)
        self.edit_song_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.edit_song_dialog.destroyed.connect(self._clear_edit_song_dialog)
        self.edit_song_dialog.show()
        self.edit_song_dialog.raise_()
        self.edit_song_dialog.activateWindow()

    def _clear_edit_song_dialog(self):
        self.edit_song_dialog = None

    def remove_song(self):
        if self.songs_list.currentItem() is None:
            return
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
        self.txt_song.setHtml(html_txt)


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


def load_custom_font_family():
    font_id = QFontDatabase.addApplicationFont("fonts/Roboto-Regular.ttf")
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            return font_families[0]

    return None


class FlowLayout(QLayout):
    """Responsive wrapping layout used by the moment filters."""
    def __init__(self, parent=None, margin=0, h_spacing=8, v_spacing=4):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _do_layout(self, rect, test_only):
        x, y, line_height = rect.x(), rect.y(), 0
        for item in self._items:
            next_x = x + item.sizeHint().width() + self._h_spacing
            if next_x - self._h_spacing > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + self._v_spacing
                next_x = x + item.sizeHint().width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y()


class SongCatalogList(QListWidget):
    """Catalogue list exporting stable song titles for external drag and drop."""
    def mimeData(self, items):
        mime = QMimeData()
        titles = []
        for item in items:
            song = item.data(Qt.ItemDataRole.UserRole)
            titles.append(song.title if song is not None else item.text())
        mime.setText("\n".join(titles))
        return mime

    def supportedDragActions(self):
        return Qt.DropAction.CopyAction


class MomentSongList(QListWidget):
    songs_dropped = pyqtSignal(object, list)
    content_changed = pyqtSignal()

    def __init__(self, moment, parent=None):
        super().__init__(parent)
        self.moment = moment
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.model().rowsInserted.connect(self.refresh_height)
        self.model().rowsRemoved.connect(self.refresh_height)
        self.model().rowsMoved.connect(self.refresh_height)
        self.refresh_height()

    def mimeData(self, items):
        mime = QMimeData()
        mime.setText("\n".join(item.text() for item in items))
        return mime

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def refresh_height(self, *args):
        count = self.count()
        self.setVisible(count > 0)
        if count:
            row_height = max(24, self.sizeHintForRow(0))
            self.setFixedHeight(count * row_height + 2 * self.frameWidth() + 4)
        else:
            self.setFixedHeight(0)
        self.content_changed.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        titles = [line.strip() for line in event.mimeData().text().splitlines() if line.strip()]
        if not titles:
            event.ignore()
            return
        source = event.source()
        if source is self:
            # Native internal move preserves the precise drop position.
            super().dropEvent(event)
            self.refresh_height()
            return
        self.songs_dropped.emit(self.moment, titles)
        # Moving between moment lists removes the original items after copying.
        if isinstance(source, MomentSongList):
            for item in list(source.selectedItems()):
                source.takeItem(source.row(item))
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        self.refresh_height()


class MomentDropFrame(QFrame):
    songs_dropped = pyqtSignal(object, list)

    def __init__(self, moment, parent=None):
        super().__init__(parent)
        self.moment = moment
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        titles = [line.strip() for line in event.mimeData().text().splitlines() if line.strip()]
        if titles:
            self.songs_dropped.emit(self.moment, titles)
            source = event.source()
            if isinstance(source, MomentSongList):
                for item in list(source.selectedItems()):
                    source.takeItem(source.row(item))
            event.acceptProposedAction()
        else:
            event.ignore()


class Launcher(QMainWindow):
    SONG_MOMENTS = [
        MassMoment.intro, MassMoment.gloria, MassMoment.offertorio,
        MassMoment.santo, MassMoment.pace, MassMoment.comunione, MassMoment.fine
    ]

    def __init__(self, file_librone="librone.json"):
        super().__init__()
        self.messa = None
        self.date = ""
        self.bible = Bible()
        self.librone = Librone(file_librone)
        self.all_songs = []
        self.moment_lists = {}
        self.lbl_canto_text = {
            MassMoment.intro: "Ingresso", MassMoment.gloria: "Gloria",
            MassMoment.offertorio: "Offertorio", MassMoment.santo: "Santo",
            MassMoment.pace: "Pace", MassMoment.comunione: "Comunione",
            MassMoment.fine: "Uscita"
        }
        self.setObjectName("launcherWindow")
        self.setWindowTitle("PresentazioniMessa")
        self.resize(1450, 820)

        self._build_toolbar()
        self._build_menu()
        self._build_main_ui()

        self.manage_songs_dialog = ManageLibrone(
            delete_song_callback=self.delete_song_callback,
            add_song_callback=self.add_song_callback,
            update_song_callback=self.update_song_callback
        )
        self.update_manager = UpdateManager()
        self.update_dialog = UpdateDialog(self.update_manager)
        self.webapp_mass = []
        self.populate_song_catalog()
        self.fetch_saved_mass_from_webapp()

    def _build_toolbar(self):
        toolbar = QToolBar("Preparazione Messa")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addWidget(QLabel("Data della Messa: "))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        
        calendar = self.date_edit.calendarWidget()
        calendar.setGridVisible(True)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { color: black; background-color: white; }
            QCalendarWidget QToolButton { color: black; background-color: #e9eef3; font-weight: bold; }
            QCalendarWidget QAbstractItemView:enabled { color: black; background-color: white;
                selection-color: white; selection-background-color: #0078d4; }
            QCalendarWidget QAbstractItemView:disabled { color: #777; }
        """)
        self.date_edit.dateChanged.connect(self.on_date_select)
        toolbar.addWidget(self.date_edit)
        toolbar.addSeparator()
        self.check_single_section = QCheckBox("Una strofa per slide")
        toolbar.addWidget(self.check_single_section)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.act_start = QAction(QIcon("start.png"), "INIZIA MESSA!", self)
        self.act_start.triggered.connect(self.on_start_messa)
        toolbar.addAction(self.act_start)
        play_button = toolbar.widgetForAction(self.act_start)
        if play_button is not None:
            play_button.setObjectName("primaryButton")

    def _build_menu(self):
        menu = self.menuBar()
        librone_menu = menu.addMenu("Librone")
        action = QAction("Gestisci Canzoni", self); action.triggered.connect(self.manage_songs); librone_menu.addAction(action)
        action = QAction("Scarica Librone", self); action.triggered.connect(self.sync_librone); librone_menu.addAction(action)
        action = QAction("Carica Librone Aggiornato", self); action.triggered.connect(self.upload_librone); librone_menu.addAction(action)
        update_menu = menu.addMenu("Aggiorna")
        action = QAction("Verifica Aggiornamenti", self); action.triggered.connect(self.check_for_updates); update_menu.addAction(action)

    def _build_main_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("launcherSplitter")

        # Left: unique searchable/filterable catalogue.
        left = QGroupBox("Librone")
        left.setObjectName("launcherCard")
        left_layout = QVBoxLayout(left)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca per titolo o numero...")
        self.search_box.textChanged.connect(self.apply_song_filters)
        left_layout.addWidget(self.search_box)
        filters = QGroupBox("Filtra per momento consigliato")
        filters.setObjectName("filterCard")
        filter_layout = FlowLayout(filters, margin=4, h_spacing=10, v_spacing=5)
        self.filter_checks = {}
        all_check = QCheckBox("Mostra tutti")
        all_check.setChecked(True)
        all_check.toggled.connect(self.on_all_filter_toggled)
        self.filter_checks[None] = all_check
        filter_layout.addWidget(all_check)
        for moment in self.SONG_MOMENTS:
            check = QCheckBox(self.lbl_canto_text[moment])
            check.toggled.connect(self.on_specific_filter_toggled)
            self.filter_checks[moment] = check
            filter_layout.addWidget(check)
        left_layout.addWidget(filters)
        self.catalog_list = SongCatalogList()
        self.catalog_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.catalog_list.setDragEnabled(True)
        self.catalog_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.catalog_list.currentItemChanged.connect(self.show_selected_song)
        left_layout.addWidget(self.catalog_list, 1)
        splitter.addWidget(left)

        # Center: song viewer.
        center = QGroupBox("Anteprima canto")
        center.setObjectName("launcherCard")
        center_layout = QVBoxLayout(center)
        self.song_title = QLabel("Seleziona un canto")
        self.song_title.setObjectName("sectionTitle")
        center_layout.addWidget(self.song_title)
        self.song_viewer = QTextEdit()
        self.song_viewer.setReadOnly(True)
        self.song_viewer.setStyleSheet("font-size: 16pt; line-height: 125%; padding: 10px;")
        center_layout.addWidget(self.song_viewer, 1)
        splitter.addWidget(center)

        # Right: Mass song structure.
        right = QGroupBox("Scaletta della Messa")
        right.setObjectName("launcherCard")
        right_layout = QVBoxLayout(right)
        hint = QLabel("Trascina uno o più canti dal Librone, oppure selezionali e premi +.")
        hint.setWordWrap(True)
        hint.setObjectName("subtleText")
        right_layout.addWidget(hint)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        body = QWidget(); self.moments_layout = QVBoxLayout(body); self.moments_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for moment in self.SONG_MOMENTS:
            box = MomentDropFrame(moment); box.setObjectName("momentCard"); box.setFrameShape(QFrame.Shape.StyledPanel)
            box_layout = QVBoxLayout(box)
            header = QHBoxLayout()
            label = QLabel(f"<b>{self.lbl_canto_text[moment]}</b>")
            header.addWidget(label, 1)
            add_button = QPushButton("+"); add_button.setObjectName("compactButton"); add_button.setFixedSize(36, 34)
            add_button.setToolTip(f"Aggiungi i canti selezionati a {self.lbl_canto_text[moment]}")
            add_button.clicked.connect(lambda checked=False, m=moment: self.add_selected_songs(m))
            remove_button = QPushButton("−"); remove_button.setObjectName("compactButton"); remove_button.setFixedSize(36, 34)
            remove_button.setToolTip("Rimuovi i canti selezionati da questo momento")
            header.addWidget(add_button); header.addWidget(remove_button)
            box_layout.addLayout(header)
            songs = MomentSongList(moment)
            songs.songs_dropped.connect(self.add_song_titles)
            box.songs_dropped.connect(self.add_song_titles)
            remove_button.clicked.connect(lambda checked=False, ls=songs: self.remove_selected_from_moment(ls))
            box_layout.addWidget(songs)
            self.moment_lists[moment] = songs
            self.moments_layout.addWidget(box)
        scroll.setWidget(body); right_layout.addWidget(scroll, 1)
        splitter.addWidget(right)
        splitter.setSizes([390, 430, 620])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        self.setCentralWidget(splitter)

    def populate_song_catalog(self):
        self.all_songs = self.librone.get_all_songs()
        self.apply_song_filters()

    def apply_song_filters(self):
        selected_title = self.catalog_list.currentItem().data(Qt.ItemDataRole.UserRole).title if self.catalog_list.currentItem() else None
        query = self.search_box.text().strip().casefold()
        active = [m for m in self.SONG_MOMENTS if self.filter_checks[m].isChecked()]
        show_all = self.filter_checks[None].isChecked() or not active
        self.catalog_list.clear()
        for song in self.all_songs:
            if query not in f"{song.number} {song.title}".casefold():
                continue
            if not show_all and not any(moment in song.tags for moment in active):
                continue
            item = QListWidgetItem(f"{song.number} - {song.title}" if song.number else song.title)
            item.setData(Qt.ItemDataRole.UserRole, song)
            item.setData(Qt.ItemDataRole.UserRole + 1, song.title)
            item.setToolTip("Momenti consigliati: " + ", ".join(self.lbl_canto_text.get(t, t.name) for t in song.tags))
            self.catalog_list.addItem(item)
            if song.title == selected_title:
                self.catalog_list.setCurrentItem(item)
        if self.catalog_list.count() and self.catalog_list.currentRow() < 0:
            self.catalog_list.setCurrentRow(0)

    def on_all_filter_toggled(self, checked):
        if checked:
            for moment in self.SONG_MOMENTS:
                self.filter_checks[moment].blockSignals(True); self.filter_checks[moment].setChecked(False); self.filter_checks[moment].blockSignals(False)
        self.apply_song_filters()

    def on_specific_filter_toggled(self):
        any_checked = any(self.filter_checks[m].isChecked() for m in self.SONG_MOMENTS)
        self.filter_checks[None].blockSignals(True); self.filter_checks[None].setChecked(not any_checked); self.filter_checks[None].blockSignals(False)
        self.apply_song_filters()

    def show_selected_song(self, current, previous=None):
        if current is None:
            self.song_title.setText("Seleziona un canto"); self.song_viewer.clear(); return
        song = current.data(Qt.ItemDataRole.UserRole)
        self.song_title.setText(f"{song.number} - {song.title}" if song.number else song.title)
        self.song_viewer.setHtml("<br><br>".join(song.get_pages(one_section_per_page=True)))

    def selected_catalog_titles(self):
        return [item.data(Qt.ItemDataRole.UserRole).title for item in self.catalog_list.selectedItems()]

    def add_selected_songs(self, moment):
        self.add_song_titles(moment, self.selected_catalog_titles())

    def add_song_titles(self, moment, titles):
        target = self.moment_lists[moment]
        existing = [target.item(i).text() for i in range(target.count())]
        for title in titles:
            # Drag text may include the displayed number prefix.
            exact = next((s.title for s in self.all_songs if title in (s.title, f"{s.number} - {s.title}")), title)
            if exact and exact not in existing:
                target.addItem(exact); existing.append(exact)

    def remove_selected_from_moment(self, target):
        for item in target.selectedItems():
            target.takeItem(target.row(item))

    def clear_mass_structure(self):
        for target in self.moment_lists.values():
            target.clear()

    def closeEvent(self, event):
        if self.messa is not None:
            self.messa.close(); self.messa = None
        for name in ("manage_songs_dialog", "update_dialog"):
            dialog = getattr(self, name, None)
            if dialog is not None: dialog.close()
        event.accept()

    def fetch_saved_mass_from_webapp(self):
        try:
            response = requests.get("https://corogiovani.pythonanywhere.com/messa/list", timeout=10)
            self.webapp_mass = response.json()
        except Exception:
            self.webapp_mass = []
        self.on_date_select()

    def load_webapp_mass(self, date):
        self.clear_mass_structure()
        if date not in self.webapp_mass:
            return
        try:
            response = requests.get(f"https://corogiovani.pythonanywhere.com/messa/{date}", timeout=10)
            songs = response.json()
            for moment_name, titles in songs.items():
                moment = MassMoment.from_name(moment_name)
                if moment in self.moment_lists:
                    self.add_song_titles(moment, titles)
        except Exception:
            pass

    def on_date_select(self):
        self.load_webapp_mass(self.date_edit.date().toString("yyyy-MM-dd"))

    def manage_songs(self):
        self.manage_songs_dialog.set_librone(self.librone.get_all_songs()); self.manage_songs_dialog.show()

    def delete_song_callback(self, title):
        if self.librone.delete_song(title):
            self.populate_song_catalog(); self.manage_songs_dialog.set_librone(self.librone.get_all_songs())

    def add_song_callback(self, title, number, moments, rits, structure):
        if self.librone.add_song(title=title, number=number, moments=moments, rits=rits, structure=structure):
            self.populate_song_catalog(); self.manage_songs_dialog.set_librone(self.librone.get_all_songs())

    def update_song_callback(self, original_title, title, number, moments, rits, structure):
        ok = self.librone.update_song(original_title, title, number, moments, rits, structure)
        if ok:
            self.populate_song_catalog()
            self.manage_songs_dialog.set_librone(self.librone.get_all_songs())
        return ok

    def sync_librone(self):
        if self.librone.check_for_updates():
            self.librone = Librone(self.librone.filename); self.populate_song_catalog()
            self.manage_songs_dialog.set_librone(self.librone.get_all_songs())

    def upload_librone(self):
        self.librone.upload_new_version()

    def check_for_updates(self):
        new_version, version = self.update_manager.check_for_updates()
        if new_version: self.update_dialog.show()

    def populate_song_lists(self, reload=False):
        # Backwards-compatible hook used by Librone management callbacks.
        self.populate_song_catalog()

    def get_data(self):
        scaletta = {moment: [self.moment_lists[moment].item(i).text() for i in range(self.moment_lists[moment].count())] for moment in self.SONG_MOMENTS}
        self.librone.load_songs(scaletta)
        songs = {moment.name: titles for moment, titles in scaletta.items()}
        self.date = self.date_edit.date().toString("yyyyMMdd")
        self.bible.fetch_online(aaaammdd=self.date)
        lectures = {moment.name: lecture.to_json() for moment, lecture in self.bible.lectures.items()}
        return songs, lectures

    def on_start_messa(self):
        self.get_data()
        self.messa = MassPresenter(aaaammdd=self.date, body_font_family=load_custom_font_family(), default_font_size=48)
        self.messa.set_bible(self.bible)
        self.messa.set_librone(self.librone)
        self.messa.run(fullscreen=True, one_section_per_page=self.check_single_section.isChecked())

    def on_close(self):
        subprocess.call("explorer messe", shell=True)


stylesheet = {
    # Button colors
    'danger': '#dc3545',
    'warning': '#ffc107',
    'success': '#13191c',
    # Font
    'background': '#000000',
}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]
                        )

    app = QApplication(sys.argv)
    apply_stylesheet(
        app,
        theme='light_lightgreen.xml',
        invert_secondary=False,
        extra={
            'density_scale': '-1',
            'font_family': 'Roboto',
            'primaryTextColor': '#26352d',
            'secondaryTextColor': '#607266',
        },
        css_file='custom.css'
    )

    # create the instance of our Window
    # window = Mass(aaaammdd="20240908")
    window = Launcher()
    window.showMaximized()

    # start the app
    sys.exit(app.exec())
