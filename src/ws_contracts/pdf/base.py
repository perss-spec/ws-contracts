"""Base PDF generator: fonts, watermark, encryption, header/footer."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fpdf import FPDF

from .styles import DIMS, FONTS, hex_to_rgb


class BasePdfGenerator:
    """Shared logic for NDA and Contract PDF generators."""

    WATERMARK_TEXT = "WOODENSHARK LLC CONFIDENTIAL"
    OWNER_PASSWORD_PREFIX = "WS"

    def __init__(self, fonts_dir: Path | str):
        self.fonts_dir = Path(fonts_dir)

    # ── Font registration ──

    def _register_fonts(self, pdf: FPDF) -> None:
        fd = self.fonts_dir
        font_files = {
            "Cambria":  ("cambria.ttf", "cambriab.ttf", "cambriai.ttf", "cambriaz.ttf"),
            "Calibri":  ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
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

    # ── PDF creation ──

    def _create_pdf(self, employee_id: str | int = "") -> FPDF:
        rnd = uuid.uuid4().hex[:8]
        owner_pw = f"{self.OWNER_PASSWORD_PREFIX}-{employee_id}-{rnd}"

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)
        pdf.set_compression(True)

        # AES-256 encryption
        from fpdf.encryption import AccessPermission
        pdf.set_encryption(
            owner_password=owner_pw,
            user_password="",
            encryption_method="AES-256",
            permissions=AccessPermission.all(),
        )

        self._register_fonts(pdf)
        return pdf

    # ── Watermark (diagonal text on every page) ──

    def _draw_watermark(self, pdf: FPDF, text: str | None = None) -> None:
        text = text or self.WATERMARK_TEXT
        with pdf.rotation(45, pdf.w / 2, pdf.h / 2):
            pdf.set_font(FONTS["HEADING"], "B", 42)
            # Simulate alpha ~0.06 with very light gray (opacity 6% of black ≈ rgb 240)
            pdf.set_text_color(230, 230, 230)
            tw = pdf.get_string_width(text)
            pdf.text(pdf.w / 2 - tw / 2, pdf.h / 2, text)

    # ── Date formatting ──

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

    # ── Number to words ──

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

    # ── Helpers ──

    @staticmethod
    def _set_color(pdf: FPDF, hex_color: str, kind: str = "text") -> None:
        r, g, b = hex_to_rgb(hex_color)
        if kind == "text":
            pdf.set_text_color(r, g, b)
        elif kind == "fill":
            pdf.set_fill_color(r, g, b)
        elif kind == "draw":
            pdf.set_draw_color(r, g, b)

    def _write_multiline(self, pdf: FPDF, text: str, w: float = 0, h: float = 5, align: str = "J") -> None:
        """Write text with automatic line wrapping."""
        if not w:
            w = DIMS["CONTENT_W"]
        pdf.multi_cell(w, h, text, align=align)
