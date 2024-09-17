import json

import gdown

from model.commons import MassMoment

librone_drive_url = "https://drive.google.com/uc?id=1aB18D_4piytDuV2fMfAp-1ByQ7kdOwV7"

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

    def __get_body_page_html(self, id):
        if id >= len(self.body):
            return ""

        verse = self.body[id]
        # Fetch and prettify the rit
        if "<RIT" in verse:
            verse = f"<b>{self.raw[verse]}</b>"

        # To HTML
        verse = verse.replace("\n", "<br>")
        return verse

    def get_pages(self, wpp=100):
        # Generate the following pages combo
        # RIT alone / RIT + verse / verse + RIT / verse alone
        pages = []
        word_count = 0

        current_page = f"<b><u>{self.title}</u></b><br>"

        for i in range(0, len(self.body), 2):

            v1 = self.__get_body_page_html(i)
            v2 = self.__get_body_page_html(i + 1)

            current_page += f"{v1}<br><br>{v2}"
            if i + 1 < len(self.body):
                current_page += "<br><br>"

            pages.append(current_page)
            current_page = ""

            # l = len(verse.split(" "))
            # if (word_count + l) > wpp:
            #     pages.append(current_page)
            #     current_page = ""
            #     word_count = 0
            #
            # word_count += l
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
            MassMoment.santo,
            MassMoment.pace,
            MassMoment.comunione,
            MassMoment.fine
        ]

    def check_for_updates(self):
        try:
            print("Try to update the Librone")
            gdown.download(librone_drive_url, "librone.json")

            with open(self.filename, 'r', encoding="utf-8") as f:
                self.librone = json.load(f)

            return True
        except Exception as e:
            print(e)
            return False

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
