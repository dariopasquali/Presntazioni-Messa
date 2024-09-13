from fpdf import FPDF


class PDFMaker:
    def __init__(self):
        self.pdf = FPDF(orientation='L', unit='pt', format=(1080, 1920))
        self.pdf.set_auto_page_break(auto=True, margin=30)  # Enable auto page break

        self.pdf.add_font("roboto", style="", fname="fonts/Roboto-Regular.ttf")
        self.pdf.add_font("roboto", style="b", fname="fonts/Roboto-Bold.ttf")
        self.pdf.add_font("roboto", style="i", fname="fonts/Roboto-Italic.ttf")
        self.pdf.add_font("roboto", style="bi", fname="fonts/Roboto-BoldItalic.ttf")

        self.filename = ""

    def set_filename(self, filename):
        self.filename = filename

    def new_page(self, html_content, font_size=45):
        self.pdf.add_page()
        self.pdf.set_fill_color(0, 0, 0)
        self.pdf.rect(0, 0, 1920, 1080, 'F')  # Draw a black rectangle as background
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_left_margin(30)
        self.pdf.set_top_margin(60)
        self.pdf.set_font("roboto", size=font_size*1.5)

        self.pdf.write_html(html_content)

    def write_pdf(self):
        self.pdf.output(self.filename)

