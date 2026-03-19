"""Base PDF generator: fonts, watermark, encryption, header/footer."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.encryption import AccessPermission

from .styles import DIMS, FONTS, hex_to_rgb


class WsPDF(FPDF):
    """Custom FPDF with header/footer/watermark support via subclassing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_title_page = True
        self._doc_type = "Document"
        self._header_color = "#1A0000"
        self._accent_color = "#C62828"
        self._header_text_color = "#D4A017"
        self._header_label = "STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED"
        self._company_color = "#8B0000"
        self._watermark_text = "WOODENSHARK LLC CONFIDENTIAL"

    def header(self):
        if self._is_title_page:
            return
        r, g, b = hex_to_rgb("#FFFFFF")
        self.set_fill_color(r, g, b)
        self.rect(0, 0, 210, 15, style="F")

        r, g, b = hex_to_rgb(self._header_color)
        self.set_fill_color(r, g, b)
        self.rect(0, 0, 210, 7, style="F")
        self.set_font(FONTS["HEADING"], "", 6)
        r, g, b = hex_to_rgb(self._header_text_color)
        self.set_text_color(r, g, b)
        self.set_xy(0, 2)
        self.cell(210, 4, self._header_label, align="C")

        self.set_font(FONTS["HEADING"], "B", 7)
        r, g, b = hex_to_rgb(self._company_color)
        self.set_text_color(r, g, b)
        self.set_xy(18, 8)
        self.cell(0, 4, "WOODENSHARK LLC")
        self.set_font(FONTS["HEADING"], "", 7)
        self.set_text_color(107, 107, 107)
        self.set_xy(0, 8)
        self.cell(192, 4, self._doc_type, align="R")

        r, g, b = hex_to_rgb(self._accent_color)
        self.set_draw_color(r, g, b)
        self.set_line_width(0.4)
        self.line(18, 13, 192, 13)

    def footer(self):
        if self._is_title_page:
            self._is_title_page = False
            return
        # Watermark first (behind content conceptually)
        self._do_watermark()

        self.set_fill_color(255, 255, 255)
        self.rect(0, 277, 210, 20, style="F")

        self.set_draw_color(208, 208, 208)
        self.set_line_width(0.15)
        self.line(18, 283, 192, 283)

        self.set_font(FONTS["HEADING"], "", 7)
        self.set_text_color(107, 107, 107)
        self.set_xy(0, 284)
        self.cell(
            210, 4,
            f"{self._doc_type}  |  STRICTLY CONFIDENTIAL  |  Page {{nb}}",
            align="C",
        )

        r, g, b = hex_to_rgb(self._header_color)
        self.set_fill_color(r, g, b)
        self.rect(0, 289, 210, 8, style="F")
        self.set_font(FONTS["HEADING"], "", 6)
        r, g, b = hex_to_rgb(self._header_text_color)
        self.set_text_color(r, g, b)
        self.set_xy(0, 291)
        self.cell(210, 4, self._header_label, align="C")

    def _do_watermark(self):
        text = self._watermark_text
        with self.rotation(45, self.w / 2, self.h / 2):
            self.set_font(FONTS["HEADING"], "B", 42)
            self.set_text_color(230, 230, 230)
            tw = self.get_string_width(text)
            self.text(self.w / 2 - tw / 2, self.h / 2, text)


class BasePdfGenerator:
    """Shared logic for NDA and Contract PDF generators."""

    WATERMARK_TEXT = "WOODENSHARK LLC CONFIDENTIAL"
    OWNER_PASSWORD_PREFIX = "WS"

    def __init__(self, fonts_dir: Path | str):
        self.fonts_dir = Path(fonts_dir)

    def _register_fonts(self, pdf: FPDF) -> None:
        fd = self.fonts_dir
        font_files = {
            "Cambria": ("cambria.ttf", "cambriab.ttf", "cambriai.ttf", "cambriaz.ttf"),
            "Calibri": ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
        }
        for family, (regular, bold, italic, bold_italic) in font_files.items():
            if (fd / regular).exists():
                pdf.add_font(family, "", str(fd / regular))
            if (fd / bold).exists():
                pdf.add_font(family, "B", str(fd / bold))
            if (fd / italic).exists():
                pdf.add_font(family, "I", str(fd / italic))
            if (fd / bold_italic).exists():
                pdf.add_font(family, "BI", str(fd / bold_italic))

    def _create_pdf(self, employee_id: str | int = "") -> WsPDF:
        rnd = uuid.uuid4().hex[:8]
        owner_pw = f"{self.OWNER_PASSWORD_PREFIX}-{employee_id}-{rnd}"

        pdf = WsPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)
        pdf.set_compression(True)
        pdf.alias_nb_pages()

        pdf.set_encryption(
            owner_password=owner_pw,
            user_password="",
            encryption_method="AES-256",
            permissions=AccessPermission.all(),
        )

        self._register_fonts(pdf)
        return pdf

    @staticmethod
    def format_date(d: date | datetime | str | None) -> str:
        if d is None:
            return ""
        if isinstance(d, str):
            try:
                d = datetime.fromisoformat(d).date()
            except ValueError:
                return d
        if isinstance(d, datetime):
            d = d.date()
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        return f"{months[d.month - 1]} {d.day}, {d.year}"

    @staticmethod
    def number_to_words(n: int | float) -> str:
        ones = [
            "", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen",
            "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
        ]
        tens_words = [
            "", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety",
        ]
        n = round(n)
        if n == 0:
            return "zero"
        if n < 20:
            return ones[n]
        if n < 100:
            return tens_words[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        if n < 1000:
            return (
                ones[n // 100] + " hundred"
                + (" " + BasePdfGenerator.number_to_words(n % 100) if n % 100 else "")
            )
        if n < 1_000_000:
            return (
                BasePdfGenerator.number_to_words(n // 1000) + " thousand"
                + (" " + BasePdfGenerator.number_to_words(n % 1000) if n % 1000 else "")
            )
        return str(n)

    @staticmethod
    def _set_color(pdf: FPDF, hex_color: str, kind: str = "text") -> None:
        r, g, b = hex_to_rgb(hex_color)
        if kind == "text":
            pdf.set_text_color(r, g, b)
        elif kind == "fill":
            pdf.set_fill_color(r, g, b)
        elif kind == "draw":
            pdf.set_draw_color(r, g, b)
