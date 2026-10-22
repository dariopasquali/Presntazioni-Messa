import enum
import re

import requests


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
    news = 21

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
            "news": MassMoment.news,
            "silence": MassMoment.silence,
        }[name]


def normalize_display_html(text):
    """Remove accidental source line breaks while preserving intentional HTML breaks."""
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*(<br\s*/?>)\s*", r"\1", text, flags=re.IGNORECASE)
    return text.strip()


class Pages:
    def __init__(self, body):
        self.body = body

    def get_pages(self, wpp=100, one_section_per_page=True, font=None, max_width=1024, max_height=768):
        body = normalize_display_html(self.body)
        # Fixed rites contain deliberate <br> tags. Keep those tags, but do not
        # turn indentation/newlines from triple-quoted strings into extra spacing.
        tokens = body.split()
        return [" ".join(tokens[i:i + wpp]) for i in range(0, len(tokens), wpp)] or [""]

class ImagePages:
    def __init__(self, content):
        self.content = content

    def get_pages(self, *args, **kwargs):
        return [self.content]


news_url = "https://corogiovani.pythonanywhere.com/get_news"
flayer_url = "https://corogiovani.pythonanywhere.com/get_flyer"


class NewsFetcher:
    @staticmethod
    def fetch_news():
        response = requests.get(news_url)
        return response.text


class FlayerFetcher:
    @staticmethod
    def fetch_flayer():
        response = requests.get(flayer_url)
        return response.content

