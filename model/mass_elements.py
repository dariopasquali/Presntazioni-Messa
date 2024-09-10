import enum

import requests
from bs4 import BeautifulSoup

import json


class MassMoment(enum.Enum):
    welcome = -1
    intro = 0  # CANTO
    confesso = 1  # RITO
    kyrie = 2  # RITO
    gloria = 3  # CANTO
    lettura_1 = 4  # LETTURA
    salmo = 5  # LETTURA
    lettura_2 = 6  # LETTURA
    alleluia = 7  # LETTURA
    vangelo = 8  # LETTURA
    credo = 9  # RITO
    offertorio = 10  # CANTO
    santo = 17  # CANTO
    padre_nostro = 11  # RITO
    pace = 12  # CANTO (Opt)
    agnello = 13  # CANTO
    invito_cena = 14  # RITO
    comunione = 15  # CANTO (x2/3)
    fine = 16  # CANTO
    silence = 20

    @staticmethod
    def from_name(name):
        return {
            "welcome": MassMoment.welcome,
            "intro": MassMoment.intro,
            "confesso": MassMoment.confesso,
            "kyrie": MassMoment.kyrie,
            "gloria": MassMoment.gloria,
            "lettura_1": MassMoment.lettura_1,
            "salmo": MassMoment.salmo,
            "lettura_2": MassMoment.lettura_2,
            "alleluia": MassMoment.alleluia,
            "vangelo": MassMoment.vangelo,
            "credo": MassMoment.credo,
            "offertorio": MassMoment.offertorio,
            "santo": MassMoment.santo,
            "padre_nostro": MassMoment.padre_nostro,
            "pace": MassMoment.pace,
            "agnello": MassMoment.agnello,
            "invito_cena": MassMoment.invito_cena,
            "comunione": MassMoment.comunione,
            "fine": MassMoment.fine,
            "silence": MassMoment.silence,
        }[name]


website_root = "https://www.lachiesa.it/calendario/{aaaammdd}.html"


class Pages:
    def __init__(self, body):
        self.body = body

    def get_pages(self, wpp=100):
        words = self.body.split(" ")
        return [" ".join(words[i:i + wpp]) for i in range(0, len(words), wpp)]


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

    def get(self, mass_moment):
        if mass_moment in self.lectures:
            return self.lectures[mass_moment]
        return None

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

        soup = BeautifulSoup(response.text,
                             "html.parser")
        lectures = soup.find_all('div', class_='section-content-testo')

        lectures = [x.find_all('p') for x in lectures]

        lecture_1 = [txt.replace("\r\n", " ") for txt in lectures[0][0].text.strip().split("\n\r\n")]
        salmo = [x.replace("\t", "").replace("\r\n", "<VERSE>").split("\n") for x in
                 lectures[1][0].text.strip().split("\n\r\n")]
        salmo = [item.replace("<VERSE>", "\n") for sub in salmo for item in sub]
        lecture_2 = [txt.replace("\r\n", " ") for txt in lectures[2][0].text.strip().split("\n\r\n")]
        gospel = [txt.replace("\r\n", " ") for txt in lectures[3][0].text.strip().split("\n\r\n")]

        alleluia = [p for p in soup.find_all('p') if 'alleluia' in p.get_text().lower()][0]

        self.lectures[MassMoment.lettura_1] = Lecture(head=lecture_1[0], body=lecture_1[1])
        self.lectures[MassMoment.lettura_2] = Lecture(head=lecture_2[0], body=lecture_2[1])
        self.lectures[MassMoment.vangelo] = Lecture(head=gospel[0], body=gospel[1], ending="Parola del Signore")
        self.lectures[MassMoment.salmo] = Salmo(rit=salmo[0], body=salmo[1:])
        self.lectures[MassMoment.alleluia] = Alleluia(body="\r\n".join(alleluia.text.split("\r\n")[1:-1]))


class Song:
    def __init__(self):
        self.title = ""
        self.number = 0
        self.body = []
        self.raw = ""

    def parse_json(self, song_json):
        self.raw = song_json
        self.title = song_json["title"]
        self.number = song_json["number"]
        self.body = song_json["body"]

    def get_pages(self, wpp=100):
        pages = []
        word_count = 0
        current_page = f"<b>{self.title}</b><br><br>"
        for verse in self.body:
            if "<RIT" in verse:
                verse = f"<b>{self.raw[verse]}</b>"
            l = len(verse.split(" "))

            if (word_count + l) > wpp:
                pages.append(current_page)
                current_page = ""
                word_count = 0

            word_count += l
            current_page += f"{verse}<br><br>"
        pages.append(current_page)
        return pages


class Librone:
    def __init__(self, filename="librone.json"):
        self.filename = filename
        self.scaletta = {}
        self.librone = None

        with open(self.filename, 'r', encoding="utf-8") as f:
            self.librone = json.load(f)

        self.moments = [
            MassMoment.intro,
            MassMoment.gloria,
            MassMoment.offertorio,
            MassMoment.pace,
            MassMoment.comunione,
            MassMoment.fine
        ]

    def get(self, mass_moment):
        if mass_moment in self.scaletta:
            return self.scaletta[mass_moment]
        return None

    def load_songs(self, scaletta=None):
        if scaletta is None:
            scaletta = {}

        for key, titles in scaletta.items():
            self.scaletta[key] = []
            for title in titles:
                print(f"Load {title} for {key}")
                self.scaletta[key].append(self.search(title=title))

    def load_songs_by_moment(self):
        song_moment_list = [(s['title'], s['tag']) for s in self.librone['songs']]
        songs = {}
        for moment in self.moments:
            songs[moment] = [title for (title, tags) in song_moment_list if moment.name in tags]

        return songs

    def search(self, title=""):
        find = [song for song in self.librone["songs"] if song["title"] == title]
        if len(find) == 1:
            song = Song()
            song.parse_json(find[0])
            return song
        return None


if __name__ == "__main__":
    librone = Librone("../librone.json")
    librone.load_songs(scaletta={
        MassMoment.intro: ["Popoli tutti"],  # C
        MassMoment.gloria: ["Gloria Mariano"],  # C
        MassMoment.offertorio: ["Cosa Offrirti"],  # C
        MassMoment.pace: ["La pace del Signore sia con te"],  # C
        MassMoment.comunione: ["Abbracciami"],  # C
        MassMoment.fine: ["Ora vado sulla mia strada"],  # C
    })
