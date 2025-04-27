import requests
from bs4 import BeautifulSoup

from model.commons import Pages, MassMoment

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

    def get_pages(self, wpp=100):
        if self.body == "":
            return [""]

        txt = f"<b>{self.head}</b>"
        txt += "<br><br>"
        txt += self.body + f"<br><br><b>{self.ending}</b>"
        words = txt.split(" ")
        return [" ".join(words[i:i + wpp]) for i in range(0, len(words), wpp)]


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

    def get_pages(self, wpp=100):
        pages = []
        for b in self.body:
            txt = f"<b>RIT: {self.rit}</b><br><br>"
            txt += b
            pages.append(txt)

        return pages


class Alleluia(Lecture):
    def __init__(self, body, head=""):
        super().__init__(body, head)

    @staticmethod
    def from_json(js):
        return Alleluia(body=js['body'])

    def to_json(self):
        return {
            "body": self.body,
        }

    def get_pages(self, wpp=100):
        alle = "<b>Alleluia, Alleluia</b><br><br>"
        alle += self.body + "<br><br>"
        alle += "<b>Alleluia</b>"
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
        response = requests.get(url)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        daily_header = soup.find_all('div', class_='section-title')
        if len(daily_header) > 0:
            self.daily_header = daily_header[0].text.strip()

        if self.daily_header != "":
            imgs = soup.find_all('img')
            imgs = [img['src'] for img in imgs if img['alt'] == "Liturgia"]
            if len(imgs) == 1:
                with open("sunday_image.jpg", "wb") as f:
                    response = requests.get(imgs[0])
                    f.write(response.content)
                    self.sunday_image_available = True

        lectures = soup.find_all('div', class_='section-content-testo')

        lectures = [x.find_all('p') for x in lectures]

        lecture_1 = [txt.replace("\r\n", " ") for txt in lectures[0][0].text.strip().split("\n\r\n")]

        salmo = [x.replace("\t", "").replace("\r\n", "<VERSE>").split("\n") for x in
                 lectures[1][0].text.strip().split("\n\r\n")]
        salmo = [item.replace("<VERSE>", "<br>") for sub in salmo for item in sub]

        if len(lectures) == 4:
            lecture_2 = [txt.replace("\r\n", " ") for txt in lectures[2][0].text.strip().split("\n\r\n")]
            gospel = [txt.replace("\r\n", " ") for txt in lectures[3][0].text.strip().split("\n\r\n")]
        else:
            lecture_2 = ["", ""]
            gospel = [txt.replace("\r\n", " ") for txt in lectures[2][0].text.strip().split("\n\r\n")]

        alleluia = [p for p in soup.find_all('p') if 'alleluia, alleluia.' in p.get_text().lower()][0]

        self.lectures[MassMoment.lettura_1] = Lecture(head=lecture_1[0], body=lecture_1[1])
        self.lectures[MassMoment.lettura_2] = Lecture(head=lecture_2[0], body=lecture_2[1])
        self.lectures[MassMoment.vangelo] = Lecture(head=gospel[0], body=gospel[1], ending="Parola del Signore")
        self.lectures[MassMoment.salmo] = Salmo(rit=salmo[0], body=salmo[1:])
        self.lectures[MassMoment.alleluia] = Alleluia(body="\r\n".join(alleluia.text.split("\r\n")[1:-1]))
