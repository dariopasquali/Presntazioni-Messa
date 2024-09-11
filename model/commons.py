import enum


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


class Pages:
    def __init__(self, body):
        self.body = body

    def get_pages(self, wpp=100):
        words = self.body.split(" ")
        return [" ".join(words[i:i + wpp]) for i in range(0, len(words), wpp)]
