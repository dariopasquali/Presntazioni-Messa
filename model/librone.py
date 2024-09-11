import json

from model.commons import MassMoment

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
            MassMoment.santo,
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