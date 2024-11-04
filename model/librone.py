import json
import os

import gdown
import requests

from model.commons import MassMoment

librone_drive_url = "https://drive.google.com/uc?id=1aB18D_4piytDuV2fMfAp-1ByQ7kdOwV7"
librone_webapp = "https://corogiovani.pythonanywhere.com/librone/json"
librone_webapp_upload = "https://corogiovani.pythonanywhere.com/librone/upload"

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
        return self

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
                current_page += "<br>"

            pages.append(current_page)
            current_page = ""
        return pages


class Librone:
    def __init__(self, filename="librone.json"):
        self.filename = filename
        self.scaletta = {}
        self.librone = {}
        self.version = 0.0

        with open(self.filename, 'r', encoding="utf-8") as f:
            self.librone = json.load(f)
            self.version = self.librone["version"]

        self.moments = [
            MassMoment.intro,
            MassMoment.gloria,
            MassMoment.offertorio,
            MassMoment.santo,
            MassMoment.pace,
            MassMoment.comunione,
            MassMoment.fine
        ]

        self.check_for_updates()

    def check_for_updates_drive(self):
        try:
            print("Check for updates")
            gdown.download(librone_drive_url, "librone.tmp.json")

            with open("librone.tmp.json", 'r', encoding="utf-8") as f:
                librone_tmp = json.load(f)

            if librone_tmp["version"] > self.version:
                print("New update found, load the new version!")
                self.version = librone_tmp["version"]
                self.librone = librone_tmp
                os.remove("librone.json")
                os.rename("librone.tmp.json", self.filename)
            else:
                os.remove("librone.tmp.json")
                print(f"No update, version: {self.version}")

            return True
        except Exception as e:
            print(e)
            return False

    def check_for_updates(self):

        # Send a GET request to the API endpoint
        response = requests.get(librone_webapp)

        # Check if the request was successful
        if response.status_code == 200:
            # Save the content to a file
            with open("librone.tmp.json", "w") as json_file:
                json_file.write(response.text)

            with open("librone.tmp.json", 'r', encoding="utf-8") as f:
                librone_tmp = json.load(f)

            if round(librone_tmp["version"], 2) > round(self.version, 2):
                print("New update found, load the new version!")
                self.version = librone_tmp["version"]
                self.librone = librone_tmp
                os.remove("librone.json")
                os.rename("librone.tmp.json", self.filename)
            else:
                os.remove("librone.tmp.json")
                print(f"No update, version: {round(self.version, 2)}")

            return True
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            print("Response:", response.text)
            return False

    def upload_new_version(self):

        with open(self.filename, 'rb') as json_file:
            files = {'file': json_file}  # Prepare the file to be sent
            response = requests.post(librone_webapp_upload, files=files)  # Send the POST request

            # Check the response from the server
            if response.status_code == 200:
                print("File uploaded successfully:", response.json())
            else:
                print(f"Failed to upload file. Status code: {response.status_code}")
                print("Response:", response.text)

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

        return self.scaletta

    def get_all_songs(self):
        ss = [Song().parse_json(js) for js in self.librone["songs"]]
        ss.sort(key=lambda x: x.title)
        return ss

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

    def add_song(self, title, number, moments, rits, structure):
        if self.search(title) is not None:
            return False

        song_dict = {
            "title": title,
            "number": number,
            "tag": moments,
        }

        for (rit, text) in rits:
            song_dict[rit] = text

        song_dict['body'] = structure

        self.version += 0.1
        self.librone['version'] = self.version
        self.librone["songs"].append(song_dict)

        with open("librone.json", 'w', encoding="utf-8") as f:
            json.dump(self.librone, f, indent=4)

        return True

    def delete_song(self, title):
        if self.search(title) is not None:
            self.librone['songs'] = [s for s in self.librone['songs'] if s['title'] != title]

            self.version += 0.1
            self.librone['version'] = self.version

            with open("librone.json", 'w', encoding="utf-8") as f:
                json.dump(self.librone, f, indent=4)

            return True

        return False
