import requests
from PyQt6.QtGui import QFontMetrics
from bs4 import BeautifulSoup

from model.commons import Pages, MassMoment, normalize_display_html

website_root = "https://www.lachiesa.it/calendario/{aaaammdd}.html"


class Lecture(Pages):
    def __init__(self, body, head="", ending="Parola di Dio"):
        super().__init__(body)
        self.head = head
        self.body = body
        self.ending = ending

    @staticmethod
    def from_json(js):
        return Lecture(head=js['head'], body=js['body'], ending=js['ending'])

    def to_json(self):
        return {
            "head": self.head,
            "body": self.body,
            "ending": self.ending
        }

    def get_pages(self, wpp=100, one_section_per_page=True, font=None, max_width=1024, max_height=768):
        """Paginate by words, never by source lines from lachiesa.it.

        The renderer performs the final visual wrapping using the actual target
        widget width. Pages therefore contain continuous prose rather than hard
        line breaks calculated with a different font size.
        """
        import math
        from PyQt6.QtGui import QTextDocument
        if not self.body:
            return [""]

        head = normalize_display_html(self.head)
        body = normalize_display_html(self.body)
        ending = normalize_display_html(self.ending)
        words = body.split()
        safe_width = max(200, int(max_width * 0.94))
        safe_height = max(200, int(max_height * 0.90))

        def fits(candidate):
            parts = []
            if head:
                parts.append(f"<b><u>{head}</u></b>")
            if candidate:
                parts.append(candidate)
            if ending:
                parts.append(f"<b>{ending}</b>")
            doc = QTextDocument()
            doc.setDefaultFont(font)
            doc.setDocumentMargin(0)
            doc.setHtml("<br>".join(parts))
            doc.setTextWidth(safe_width)
            return doc.size().height() <= safe_height

        pages, current = [], []
        for word in words:
            candidate = current + [word]
            if current and not fits(" ".join(candidate)):
                pages.append(current)
                current = [word]
            else:
                current = candidate
        if current:
            pages.append(current)

        # Rebalance pages to avoid a very short final page.
        if len(pages) > 1:
            all_words = [word for page in pages for word in page]
            target = math.ceil(len(all_words) / len(pages))
            balanced = [all_words[i:i + target] for i in range(0, len(all_words), target)]
            if len(balanced) == len(pages) and all(fits(" ".join(page)) for page in balanced):
                pages = balanced

        rendered = []
        for page_index, page_words in enumerate(pages or [[]]):
            parts = []
            if page_index == 0 and head:
                parts.append(f"<b><u>{head}</u></b>")
            parts.append(" ".join(page_words))
            if page_index == len(pages) - 1 and ending:
                parts.append(f"<b>{ending}</b>")
            rendered.append("<br>".join(part for part in parts if part))
        return rendered or [""]



class Salmo(Lecture):
    def __init__(self, body, head="", rit=""):
        super().__init__(body, head)
        self.rit = rit

    def to_json(self):
        return {
            "rit": self.rit,
            "body": self.body,
        }

    @staticmethod
    def from_json(js):
        return Salmo(rit=js['rit'], body=js['body'])

    def get_pages(self, wpp=100, one_section_per_page=True, font=None, max_width=1024, max_height=768):
        pages = []
        for b in self.body:
            txt = f"<b><u>RIT: {self.rit}</u></b><br><br>"
            txt += b
            pages.append(txt)

        return pages


class Alleluia(Lecture):
    def __init__(self, body, head="", before="<b>Alleluia, Alleluia</b><br><br>", after="<b>Alleluia</b>"):
        super().__init__(body, head)
        self.before = before
        self.after = after

    @staticmethod
    def from_json(js):
        return Alleluia(body=js['body'])

    def to_json(self):
        return {
            "body": self.body,
        }

    def get_pages(self, wpp=100, one_section_per_page=True, font=None, max_width=1024, max_height=768):
        alle = self.before
        alle += self.body + "<br><br>"
        alle += self.after
        return [alle]


class AlleluiaQuaresima(Lecture):
    def __init__(self, body, head=""):
        super().__init__(body, head)

    @staticmethod
    def from_json(js):
        return AlleluiaQuaresima(body=js['body'])

    def to_json(self):
        return {
            "body": self.body,
        }

    def get_pages(self, wpp=100, one_section_per_page=True, font=None, max_width=1024, max_height=768):
        alle = "<b>Lode a te o Cristo, re di eterna gloria</b><br><b>Lode a te o Cristo, parola di Dio con noi!</b><br><br>"
        alle += self.body + "<br><br>"
        alle += "<b>Lode a te o Cristo, re di eterna gloria</b><br><b>Lode a te o Cristo, parola di Dio con noi!</b>"
        return [alle]


class Bible:
    def __init__(self):
        self.lectures = {
            MassMoment.lettura_1: None,
            MassMoment.salmo: None,
            MassMoment.lettura_2: None,
            MassMoment.alleluia: None,
            MassMoment.vangelo: None,
        }

        self.daily_header = ""
        self.sunday_image_available = False

    def get(self, mass_moment):
        if mass_moment in self.lectures:
            return self.lectures[mass_moment]
        return None

    def get_cover_slide(self):
        return self.daily_header, self.sunday_image_available, "sunday_image.jpg"

    def load_json(self, bible_json):
        for moment_name, lect in bible_json.items():
            self.lectures[MassMoment.from_name(moment_name)] = lect

        for moment, lect_json in self.lectures.items():
            if moment == MassMoment.salmo:
                self.lectures[moment] = Salmo.from_json(lect_json)
            elif moment == MassMoment.alleluia:
                self.lectures[moment] = Alleluia.from_json(lect_json)
            else:
                self.lectures[moment] = Lecture.from_json(lect_json)

    def fetch_online(self, aaaammdd="20240101"):
        url = website_root.format(aaaammdd=aaaammdd)
        response = requests.get(url, verify=False)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        daily_header = soup.find_all('div', class_='section-title')
        if len(daily_header) > 0:
            self.daily_header = daily_header[0].text.strip()

        try:
            if self.daily_header != "":
                imgs = soup.find_all('img')
                imgs = [img['src'] for img in imgs if img['alt'] == "Liturgia"]
                if len(imgs) == 1:
                    with open("sunday_image.jpg", "wb") as f:
                        response = requests.get(imgs[0])
                        f.write(response.content)
                        self.sunday_image_available = True
        except Exception as e:
            print(e)
            self.sunday_image_available = False

        lectures = soup.find_all('div', class_='section-content-testo')

        lectures = [x.find_all('p') for x in lectures]

        lecture_1 = [normalize_display_html(txt) for txt in lectures[0][0].text.strip().split("\n\r\n")]

        salmo = [x.replace("\t", "").replace("\r\n", "<VERSE>").split("\n") for x in
                 lectures[1][0].text.strip().split("\n\r\n")]
        salmo = [item.replace("<VERSE>", "<br>") for sub in salmo for item in sub]

        if len(lectures) == 4:
            lecture_2 = [normalize_display_html(txt) for txt in lectures[2][0].text.strip().split("\n\r\n")]
            gospel = [normalize_display_html(txt) for txt in lectures[3][0].text.strip().split("\n\r\n")]
        else:
            lecture_2 = ["", ""]
            gospel = [normalize_display_html(txt) for txt in lectures[2][0].text.strip().split("\n\r\n")]

        self.lectures[MassMoment.lettura_1] = Lecture(head=lecture_1[0], body=lecture_1[1])
        self.lectures[MassMoment.lettura_2] = Lecture(head=lecture_2[0], body=lecture_2[1])
        self.lectures[MassMoment.vangelo] = Lecture(head=gospel[0], body=gospel[1], ending="Parola del Signore")
        self.lectures[MassMoment.salmo] = Salmo(rit=salmo[0], body=salmo[1:])

        if "quaresima" in self.daily_header.lower():
            if "domenica" in self.daily_header.lower():
                search_for = 'lode a te, o cristo'
                before = "<b>Lode a te o Cristo, re di eterna gloria</b><br><b>Lode a te o Cristo, parola di Dio con noi!</b><br><br>"
                after = "<b>Lode a te o Cristo, re di eterna gloria</b><br><b>Lode a te o Cristo, parola di Dio con noi!</b>"
            else:
                search_for = 'lode e onore a te,'
                before = "<b>Lode e onore a te, Signore Gesù</b><br><br>"
                after = "<b>Lode e onore a te, Signore Gesù</b>"
        else:
            search_for = 'alleluia, alleluia.'
            before = "<b>Alleluia, Alleluia</b><br><br>"
            after = "<b>Alleluia</b>"

        alleluia = [p for p in soup.find_all('p') if search_for in p.get_text().lower()]
        if alleluia:
            txt = "\r\n".join(alleluia[0].text.split("\r\n")[1:-1])
        else:
            txt = ""
            before = "<b>Alleluia, Alleluia</b><br><br>"
            after = "<b>Alleluia</b>"

        self.lectures[MassMoment.alleluia] = Alleluia(body=txt, before=before, after=after)

