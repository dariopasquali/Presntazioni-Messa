import os
import subprocess
import sys

import gdown
from PyQt6.QtCore import QObject

version_file_drive_url = "https://drive.google.com/uc?id=1rRuHqQm06fYeJTxXEE7tEI4GgHoY5t8u"
installer_drive_url = "https://drive.google.com/uc?id=11sqdEycFOExTEvT0bQFtjG6lRtaOJC20"


class UpdateManager(QObject):
    def __init__(self):
        super().__init__()
        self.version = 0.0

        if os.path.exists("installer.exe"):
            os.remove("installer.exe")

        with open("version.txt", "r") as f:
            vf = f.readlines()
            self.version = float(vf[0])

    def check_for_updates(self, overwrite_version=False):
        print("Check for updates")
        gdown.download(version_file_drive_url, "version.tmp.txt")

        with open("version.tmp.txt", "r") as f:
            vf = f.readlines()
            v = float(vf[0])

        if overwrite_version:
            self.version = v
            with open("version.txt", "w") as f:
                f.write(str(self.version))

        os.remove("version.tmp.txt")
        return v > self.version, v

    def update(self):
        self.check_for_updates(overwrite_version=True)
        print("Start Downloading the new version!")
        gdown.download(installer_drive_url, "installer.exe")
        subprocess.Popen("installer.exe", shell=True)
        sys.exit(0)

