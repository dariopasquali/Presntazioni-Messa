from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QFont, QKeyEvent, QKeySequence, QShortcut, QTextDocument, QPainter, QAbstractTextDocumentLayout, QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSplitter, QVBoxLayout, QWidget, QScrollArea, QSizePolicy, QDialog, QLineEdit,
    QListWidget, QDialogButtonBox, QMessageBox, QListWidgetItem
)

from model.commons import MassMoment, Pages, NewsFetcher, FlayerFetcher, ImagePages, normalize_display_html
from model.rfixed_rites import *


MOMENT_LABELS = {
    MassMoment.welcome: "Copertina",
    MassMoment.intro: "Canto d'ingresso",
    MassMoment.silence: "Schermata vuota",
    MassMoment.confesso: "Confesso",
    MassMoment.kyrie: "Kyrie",
    MassMoment.gloria: "Gloria",
    MassMoment.lettura_1: "Prima lettura",
    MassMoment.salmo: "Salmo",
    MassMoment.lettura_2: "Seconda lettura",
    MassMoment.alleluia: "Alleluia",
    MassMoment.vangelo: "Vangelo",
    MassMoment.credo: "Credo",
    MassMoment.offertorio: "Offertorio",
    MassMoment.santo: "Santo",
    MassMoment.padre_nostro: "Padre nostro",
    MassMoment.pace: "Pace",
    MassMoment.agnello: "Agnello di Dio",
    MassMoment.invito_cena: "Invito alla cena",
    MassMoment.comunione: "Comunione",
    MassMoment.news: "Avvisi",
    MassMoment.fine: "Canto finale",
}


@dataclass
class PresentationSlide:
    content: object
    moment: MassMoment
    title: str
    source_index: int = 0
    local_page_index: int = 0


class PresentationController(QObject):
    slide_changed = pyqtSignal(int, object)
    structure_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.slides = []
        self.current_index = 0

    @property
    def current_slide(self):
        return self.slides[self.current_index] if self.slides else None

    @property
    def next_slide_item(self):
        if self.current_index + 1 < len(self.slides):
            return self.slides[self.current_index + 1]
        return None

    def set_slides(self, slides):
        self.slides = slides
        self.current_index = 0
        self.structure_changed.emit()
        self.emit_current()

    def emit_current(self):
        if self.slides:
            self.slide_changed.emit(self.current_index, self.slides[self.current_index])

    def next(self):
        if self.current_index < len(self.slides) - 1:
            self.current_index += 1
            self.emit_current()

    def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.emit_current()

    def go_to(self, index):
        if 0 <= index < len(self.slides):
            self.current_index = index
            self.emit_current()


class SlideView(QWidget):
    """Exact text renderer: the same QTextDocument is measured and painted."""
    def __init__(self, font_family=None, font_size=43, auto_fit=True):
        super().__init__()
        self.font_family = font_family
        self.base_font_size = font_size
        self.manual_zoom = 0
        self.auto_fit = auto_fit
        self._content = ""
        self._raw_image = None
        self._document = QTextDocument(self)
        self._document.setDocumentMargin(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(100, 100)

    def show_content(self, content):
        self._content = content
        self._raw_image = None
        if isinstance(content, str):
            self._set_document_content(content)
            self.fit_text()
        elif content:
            pixmap = QPixmap()
            if pixmap.loadFromData(content):
                self._raw_image = pixmap
        self.update()

    def _set_document_content(self, content):
        # Existing content mixes simple HTML with legacy **bold** markers.
        import re
        text = normalize_display_html(content or "")
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
        # Compact block wrapper removes QTextDocument's default paragraph margins.
        text = '<div style="margin:0; padding:0; line-height:100%;">' + text + '</div>'
        self._document.setHtml(text)

    def set_manual_zoom(self, value):
        self.manual_zoom = value
        self.fit_text()

    def _fits(self, point_size, width, height):
        self._document.setDefaultFont(QFont(self.font_family, point_size))
        self._document.setTextWidth(width)
        layout = self._document.documentLayout()
        return layout.documentSize().height() <= height

    def fit_text(self):
        if not isinstance(self._content, str) or not self._content:
            self.update()
            return
        # Safety area prevents clipping caused by screen scaling/font hinting.
        width = max(80, self.width() - 56)
        height = max(80, self.height() - 44)
        if self.auto_fit:
            low, high, best = 8, 180, 8
            while low <= high:
                size = (low + high) // 2
                if self._fits(size, width, height):
                    best = size
                    low = size + 1
                else:
                    high = size - 1
            size = max(8, best + self.manual_zoom)
        else:
            size = max(8, self.base_font_size + self.manual_zoom)
        self._document.setDefaultFont(QFont(self.font_family, size))
        self._document.setTextWidth(width)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("black"))
        if self._raw_image and not self._raw_image.isNull():
            target = self._raw_image.size()
            target.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x = (self.width() - target.width()) // 2
            y = (self.height() - target.height()) // 2
            painter.drawPixmap(x, y, target.width(), target.height(), self._raw_image)
            return
        if not isinstance(self._content, str) or not self._content:
            return
        doc_size = self._document.documentLayout().documentSize()
        left = 28
        top = max(22, (self.height() - doc_size.height()) / 2)
        painter.save()
        painter.translate(left, top)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette.setColor(QPalette.ColorRole.Text, QColor("white"))
        self._document.documentLayout().draw(painter, context)
        painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_text()


class ProjectionWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, font_family=None, font_size=43):
        super().__init__()
        self.setObjectName("projectionWindow")
        self.setWindowTitle("PresentazioniMessa - Proiezione")
        self.view = SlideView(font_family, font_size)
        self.setCentralWidget(self.view)
        self.setStyleSheet("QMainWindow#projectionWindow, QMainWindow#projectionWindow QWidget { background: black; color: white; border: none; }")
        self.is_blacked_out = False
        self.last_content = ""
        self.manual_zoom = 0

    def display_slide(self, slide):
        self.last_content = slide.content if slide else ""
        if not self.is_blacked_out:
            self.view.show_content(self.last_content)

    def set_blackout(self, active):
        self.is_blacked_out = active
        self.view.show_content("") if active else self.view.show_content(self.last_content)

    def zoom_in(self):
        self.manual_zoom = min(60, self.manual_zoom + 2)
        self.view.set_manual_zoom(self.manual_zoom)

    def zoom_out(self):
        self.manual_zoom = max(-60, self.manual_zoom - 2)
        self.view.set_manual_zoom(self.manual_zoom)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.showNormal()
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_VolumeUp, Qt.Key.Key_Plus):
            self.zoom_in()
        elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_VolumeDown, Qt.Key.Key_Minus):
            self.zoom_out()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class AddSongDialog(QDialog):
    def __init__(self, librone, available_moments, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi canto alla presentazione")
        self.resize(620, 560)
        self.songs = librone.get_all_songs() if librone else []
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Momento della Messa:"))
        self.moment_combo = QComboBox()
        for moment in available_moments:
            self.moment_combo.addItem(MOMENT_LABELS.get(moment, moment.name), moment)
        layout.addWidget(self.moment_combo)
        layout.addWidget(QLabel("Cerca nel Librone:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Titolo o numero del canto...")
        layout.addWidget(self.search)
        self.results = QListWidget()
        layout.addWidget(self.results, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search.textChanged.connect(self.populate)
        self.results.itemDoubleClicked.connect(lambda _: self.accept())
        self.populate("")
        self.search.setFocus()

    def populate(self, query):
        query = query.strip().casefold()
        self.results.clear()
        for song in self.songs:
            haystack = f"{song.number} {song.title}".casefold()
            if query in haystack:
                item = QListWidgetItem(f"{song.number} - {song.title}" if song.number else song.title)
                item.setData(Qt.ItemDataRole.UserRole, song)
                tags = ", ".join(MOMENT_LABELS.get(tag, tag.name) for tag in song.tags)
                item.setToolTip(f"Momenti consigliati: {tags}" if tags else "Nessun momento consigliato")
                self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def selected_song(self):
        item = self.results.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def selected_moment(self):
        return self.moment_combo.currentData()

    def accept(self):
        if self.selected_song() is None:
            QMessageBox.information(self, "Seleziona un canto", "Seleziona un canto da aggiungere.")
            return
        super().accept()


class ControlWindow(QMainWindow):
    closing = pyqtSignal()
    repaginate_requested = pyqtSignal()
    add_song_requested = pyqtSignal(object, object)

    def __init__(self, controller, projection, date, librone=None):
        super().__init__()
        self.controller = controller
        self.projection = projection
        self.librone = librone
        self.page_buttons = {}
        self.setObjectName("controlWindow")
        self.setWindowTitle(f"PresentazioniMessa - Regia - {date}")
        self.resize(1250, 800)
        root = QWidget()
        main = QVBoxLayout(root)

        top = QHBoxLayout()
        self.lbl_status = QLabel("Pronto")
        self.lbl_status.setObjectName("controlStatus")
        top.addWidget(self.lbl_status, 1)
        top.addWidget(QLabel("Schermo di proiezione:"))
        self.screen_combo = QComboBox()
        for i, screen in enumerate(QApplication.screens()):
            g = screen.geometry()
            marker = " (principale)" if screen == QApplication.primaryScreen() else ""
            self.screen_combo.addItem(f"{i + 1} - {screen.name()} - {g.width()}x{g.height()}{marker}", screen)
        top.addWidget(self.screen_combo)
        main.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        preview_container = QWidget()
        previews = QVBoxLayout(preview_container)
        previews.addWidget(QLabel("SLIDE CORRENTE"))
        self.current_preview = SlideView(projection.view.font_family, 22)
        self.current_preview.setMinimumHeight(260)
        previews.addWidget(self.current_preview, 2)
        previews.addWidget(QLabel("PROSSIMA SLIDE"))
        self.next_preview = SlideView(projection.view.font_family, 15)
        self.next_preview.setMinimumHeight(170)
        previews.addWidget(self.next_preview, 1)
        splitter.addWidget(preview_container)

        scale_container = QWidget()
        scale_layout = QVBoxLayout(scale_container)
        scale_layout.addWidget(QLabel("SCALETTA: elementi in verticale, pagine in orizzontale"))
        self.scale_scroll = QScrollArea()
        self.scale_scroll.setWidgetResizable(True)
        self.scale_body = QWidget()
        self.scale_grid = QVBoxLayout(self.scale_body)
        self.scale_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scale_scroll.setWidget(self.scale_body)
        scale_layout.addWidget(self.scale_scroll)
        splitter.addWidget(scale_container)
        splitter.setSizes([720, 530])
        main.addWidget(splitter, 1)

        controls = QHBoxLayout()
        reminder = QLabel(
            "Navigazione: ← → / PagSu PagGiù / Spazio    "
            "Zoom: ↑ ↓ / Volume + Volume −    "
            "Oscuramento rapido: B"
        )
        reminder.setObjectName("subtleText")
        reminder.setWordWrap(True)
        controls.addWidget(reminder, 1)
        self.btn_black = QPushButton("Oscura schermo")
        self.btn_black.setObjectName("blackoutButton")
        self.btn_black.setCheckable(True)
        self.btn_black.toggled.connect(self.toggle_blackout)
        controls.addWidget(self.btn_black)
        main.addLayout(controls)
        self.setCentralWidget(root)

        controller.slide_changed.connect(self.on_slide_changed)
        controller.structure_changed.connect(self.populate_scale)
        self.screen_combo.currentIndexChanged.connect(self.move_projection)
        shortcuts = (
            ("Right", controller.next), ("PageDown", controller.next), ("Space", controller.next),
            ("Left", controller.previous), ("PageUp", controller.previous), ("Backspace", controller.previous),
            ("Up", projection.zoom_in), ("Volume Up", projection.zoom_in),
            ("Down", projection.zoom_out), ("Volume Down", projection.zoom_out),
            ("B", self.btn_black.toggle),
        )
        self._shortcuts = []
        for sequence, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def open_add_song_dialog(self, moment=None):
        if self.librone is None:
            QMessageBox.warning(self, "Librone non disponibile", "Il Librone non è stato caricato.")
            return
        moments = [m for m in MOMENT_LABELS if m not in (MassMoment.welcome, MassMoment.silence)]
        dialog = AddSongDialog(self.librone, moments, self)
        if moment is not None:
            moment_index = dialog.moment_combo.findData(moment)
            if moment_index >= 0:
                dialog.moment_combo.setCurrentIndex(moment_index)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_song_requested.emit(dialog.selected_moment(), dialog.selected_song())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_VolumeUp, Qt.Key.Key_Plus):
            self.projection.zoom_in()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_VolumeDown, Qt.Key.Key_Minus):
            self.projection.zoom_out()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.closing.emit()
        self.projection.close()
        super().closeEvent(event)

    def populate_scale(self):
        while self.scale_grid.count():
            item = self.scale_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.page_buttons.clear()

        # Preserve presentation order, but group all consecutive elements by Mass moment.
        moment_groups = []
        for index, slide in enumerate(self.controller.slides):
            if slide.moment == MassMoment.silence:
                moment_groups.append((MassMoment.silence, []))
                continue
            if not moment_groups or moment_groups[-1][0] != slide.moment:
                moment_groups.append((slide.moment, []))
            moment_groups[-1][1].append((index, slide))

        for moment, moment_slides in moment_groups:
            if moment == MassMoment.silence:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet("margin: 7px 4px; color: #9a9a9a;")
                self.scale_grid.addWidget(separator)
                continue

            group = QFrame()
            group.setObjectName("controlMomentCard")
            group.setFrameShape(QFrame.Shape.StyledPanel)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(8, 6, 8, 8)
            group_layout.setSpacing(5)

            header = QHBoxLayout()
            title = QLabel(f"<b>{MOMENT_LABELS.get(moment, moment.name)}</b>")
            title.setStyleSheet("font-size: 11pt; font-weight: bold;")
            header.addWidget(title, 1)
            if moment not in (MassMoment.welcome, MassMoment.silence):
                add_button = QPushButton("+")
                add_button.setObjectName("compactButton")
                add_button.setToolTip(f"Aggiungi un canto a {MOMENT_LABELS.get(moment, moment.name)}")
                add_button.setFixedSize(36, 34)
                add_button.clicked.connect(lambda checked=False, m=moment: self.open_add_song_dialog(m))
                header.addWidget(add_button)
            group_layout.addLayout(header)

            elements = []
            for slide_index, slide in moment_slides:
                key = (slide.title, slide.source_index)
                if not elements or elements[-1][0] != key:
                    elements.append((key, []))
                elements[-1][1].append((slide_index, slide))

            for (element_title, _), pages in elements:
                row_widget = QWidget()
                row_widget.setMinimumHeight(42)
                row = QHBoxLayout(row_widget)
                row.setContentsMargins(4, 4, 4, 6)
                row.setSpacing(4)
                label = QLabel(element_title)
                label.setMinimumWidth(170)
                label.setWordWrap(True)
                row.addWidget(label)
                for page_number, (slide_index, _) in enumerate(pages, start=1):
                    button = QPushButton(str(page_number))
                    button.setObjectName("pageButton")
                    button.setToolTip(f"Vai alla slide {slide_index + 1}")
                    button.setFixedSize(38, 32)
                    button.clicked.connect(lambda checked=False, i=slide_index: self.controller.go_to(i))
                    row.addWidget(button)
                    self.page_buttons[slide_index] = button
                row.addStretch(1)
                group_layout.addWidget(row_widget)
            self.scale_grid.addWidget(group)

    def on_slide_changed(self, index, slide):
        self.projection.display_slide(slide)
        self.current_preview.show_content(slide.content)
        upcoming = self.controller.next_slide_item
        self.next_preview.show_content(upcoming.content if upcoming else "")
        moment = MOMENT_LABELS.get(slide.moment, slide.moment.name)
        self.lbl_status.setText(f"{moment} | {slide.title} | Slide {index + 1}/{len(self.controller.slides)}")
        for slide_index, button in self.page_buttons.items():
            button.setObjectName("currentPageButton" if slide_index == index else "pageButton")
            button.style().unpolish(button)
            button.style().polish(button)
        active = self.page_buttons.get(index)
        if active:
            self.scale_scroll.ensureWidgetVisible(active, 30, 30)

    def toggle_blackout(self, active):
        self.projection.set_blackout(active)
        self.btn_black.setText("Ripristina proiezione" if active else "Oscura schermo")

    def move_projection(self, combo_index):
        screen = self.screen_combo.itemData(combo_index)
        if screen is None:
            return
        self.projection.showNormal()
        handle = self.projection.windowHandle()
        if handle:
            handle.setScreen(screen)
        geometry = screen.geometry()
        self.projection.setGeometry(geometry)
        if len(QApplication.screens()) > 1:
            self.projection.showFullScreen()
        else:
            self.projection.resize(max(900, int(geometry.width() * .8)), max(600, int(geometry.height() * .8)))
            self.projection.move(geometry.x() + 30, geometry.y() + 30)
            self.projection.show()
        self.activateWindow()
        if self.controller.slides:
            QTimer.singleShot(150, self.repaginate_requested.emit)


class MassPresenter(QObject):
    """Facade compatible con il vecchio launcher, ora con regia e proiezione separate."""
    def __init__(self, aaaammdd, body_font_family=None, default_font_size=43):
        super().__init__()
        self.date = aaaammdd
        self.bible = None
        self.librone = None
        self.one_section_per_page = False
        self.body_font_family = body_font_family
        self.default_font_size = default_font_size
        self.controller = PresentationController()
        self.controller.setParent(self)
        self.projection = ProjectionWindow(body_font_family, default_font_size)
        self.control = ControlWindow(self.controller, self.projection, aaaammdd)
        self.control.repaginate_requested.connect(self.build_slides)
        self.control.add_song_requested.connect(self.add_song_live)

        self.sequence = [
            MassMoment.intro, MassMoment.silence, MassMoment.confesso, MassMoment.silence,
            MassMoment.kyrie, MassMoment.silence, MassMoment.gloria, MassMoment.silence,
            MassMoment.lettura_1, MassMoment.salmo, MassMoment.lettura_2,
            MassMoment.alleluia, MassMoment.vangelo, MassMoment.silence,
            MassMoment.credo, MassMoment.silence, MassMoment.offertorio,
            MassMoment.silence, MassMoment.santo, MassMoment.silence,
            MassMoment.padre_nostro, MassMoment.silence, MassMoment.pace,
            MassMoment.silence, MassMoment.agnello, MassMoment.silence,
            MassMoment.invito_cena, MassMoment.silence, MassMoment.comunione,
            MassMoment.silence, MassMoment.news, MassMoment.silence, MassMoment.fine
        ]
        self.mass_structure = {
            MassMoment.intro: [], MassMoment.confesso: [Pages(body=confesso)],
            MassMoment.kyrie: [Pages(body=kyrie)], MassMoment.gloria: [],
            MassMoment.lettura_1: [], MassMoment.salmo: [], MassMoment.lettura_2: [],
            MassMoment.alleluia: [], MassMoment.vangelo: [],
            MassMoment.credo: [Pages(body=credo_apostolico), Pages(body=credo_apostolico_2),
                               Pages(body=credo_tradizionale), Pages(body=credo_tradizionale_2),
                               Pages(body=credo_tradizionale_3), Pages(body=credo_tradizionale_4)],
            MassMoment.offertorio: [], MassMoment.santo: [],
            MassMoment.padre_nostro: [Pages(body=padre_nostro)], MassMoment.pace: [],
            MassMoment.agnello: [Pages(body=agnello)],
            MassMoment.invito_cena: [Pages(body=invito_cena)],
            MassMoment.comunione: [],
            MassMoment.news: [Pages(body=NewsFetcher.fetch_news()), ImagePages(content=FlayerFetcher.fetch_flayer())],
            MassMoment.fine: [],
        }
        self.cover_header = ""
        self.cover_pixmap_path = None

    def set_bible(self, bible):
        self.bible = bible
        for moment in (MassMoment.lettura_1, MassMoment.salmo, MassMoment.lettura_2,
                       MassMoment.alleluia, MassMoment.vangelo):
            element = bible.get(moment)
            self.mass_structure[moment] = [element] if element is not None else []
        header, image_available, image_filename = bible.get_cover_slide()
        self.cover_header = header
        self.cover_pixmap_path = image_filename if image_available else None

    def set_librone(self, librone):
        self.librone = librone
        self.control.librone = librone
        for moment in (MassMoment.intro, MassMoment.gloria, MassMoment.offertorio,
                       MassMoment.santo, MassMoment.pace, MassMoment.comunione, MassMoment.fine):
            self.mass_structure[moment] = librone.get(moment) or []

    def _element_title(self, element, moment, source_index):
        if hasattr(element, "title") and element.title:
            return element.title
        label = MOMENT_LABELS.get(moment, moment.name)
        return label if source_index == 0 else f"{label} {source_index + 1}"

    def _cover_slide(self):
        if self.cover_pixmap_path:
            pixmap = QPixmap(self.cover_pixmap_path)
            if not pixmap.isNull():
                from PyQt6.QtCore import QBuffer, QIODevice
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")
                return PresentationSlide(bytes(buffer.data()), MassMoment.welcome, "Copertina")
        return PresentationSlide(self.cover_header, MassMoment.welcome, "Copertina")

    def add_song_live(self, moment, song):
        if moment not in self.mass_structure:
            self.mass_structure[moment] = []
        self.mass_structure[moment].append(song)
        # build_slides preserves the currently projected slide by its stable key.
        self.build_slides()

    def build_slides(self):
        previous = self.controller.current_slide
        previous_key = None
        if previous is not None:
            previous_key = (previous.moment, previous.title, previous.source_index, previous.local_page_index)
        slides = [self._cover_slide()]
        font = QFont(self.body_font_family, self.default_font_size)
        width = max(640, self.projection.view.width() - 40)
        height = max(480, self.projection.view.height() - 40)
        for moment in self.sequence:
            if moment == MassMoment.silence:
                slides.append(PresentationSlide("", moment, "Schermata vuota"))
                continue
            elements = self.mass_structure.get(moment, [])
            if not elements:
                slides.append(PresentationSlide("", moment, MOMENT_LABELS.get(moment, moment.name)))
                continue
            for source_index, element in enumerate(elements):
                title = self._element_title(element, moment, source_index)
                pages = element.get_pages(
                    font=font, max_width=width, max_height=height, wpp=80,
                    one_section_per_page=self.one_section_per_page
                )
                for page_index, content in enumerate(pages or [""]):
                    slides.append(PresentationSlide(content, moment, title, source_index, page_index))
        self.controller.set_slides(slides)
        if previous_key is not None:
            for index, slide in enumerate(slides):
                key = (slide.moment, slide.title, slide.source_index, slide.local_page_index)
                if key == previous_key:
                    self.controller.go_to(index)
                    break

    def run(self, fullscreen=True, one_section_per_page=False, on_close=lambda: None):
        self.one_section_per_page = one_section_per_page
        self.control.showMaximized()
        screens = QApplication.screens()
        default_index = 0
        if len(screens) > 1:
            primary = QApplication.primaryScreen()
            default_index = next((i for i, screen in enumerate(screens) if screen != primary), 1)
        self.control.screen_combo.setCurrentIndex(default_index)
        self.control.move_projection(default_index)
        # Build only after the projection window has its final screen geometry.
        QTimer.singleShot(150, self.build_slides)

    def close(self):
        self.projection.close()
        self.control.close()

    # Compatibility helpers
    def on_right(self):
        self.controller.next()

    def on_left(self):
        self.controller.previous()
