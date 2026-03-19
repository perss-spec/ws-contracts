"""
Standalone PDF generators for Odoo module.
Combines models + base + nda + contract from ws_contracts package.
No dependency on ws_contracts — everything self-contained.

v2: Parameterized via CompanyTheme/TemplateData, bilingual rendering support.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from fpdf import FPDF
from fpdf.encryption import AccessPermission

from .theme import (
    CompanyTheme, SectionData, TemplateData,
    NDA_PALETTE, CONTRACT_PALETTE,
    default_nda_template, default_contract_template,
)


# ══════════════════════════════════════════════════
#  Models
# ══════════════════════════════════════════════════

class EmployeeData:
    """Simple data container — no pydantic dependency needed in Odoo."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 0)
        self.full_name_lat = kwargs.get("full_name_lat", "")
        self.date_of_birth = self._to_date(kwargs.get("date_of_birth"))
        self.passport_number = kwargs.get("passport_number", "")
        self.passport_issued = self._to_date(kwargs.get("passport_issued"))
        self.passport_expires = self._to_date(kwargs.get("passport_expires"))
        self.address = kwargs.get("address", "")
        self.work_email = kwargs.get("work_email", "")
        self.phone = kwargs.get("phone", "")
        self.iban = kwargs.get("iban", "")
        self.swift = kwargs.get("swift", "UNJSUAUKXXX")
        self.receiver_name = kwargs.get("receiver_name", "")
        self.rate_usd = float(kwargs.get("rate_usd") or 0)
        self.service_description = kwargs.get("service_description", "UAV Systems Development Services")
        self.agreement_date = self._to_date(kwargs.get("agreement_date"))
        self.effective_date = self._to_date(kwargs.get("effective_date"))

    @staticmethod
    def _to_date(v) -> Optional[date]:
        if not v:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v).date()
            except ValueError:
                return date.fromisoformat(v)
        return None

    def validate_for_nda(self) -> list[str]:
        checks = {
            "Full Name (Latin)": self.full_name_lat,
            "Date of Birth": self.date_of_birth,
            "Passport Number": self.passport_number,
            "Passport Issued": self.passport_issued,
            "Passport Expires": self.passport_expires,
            "Address": self.address,
        }
        return [k for k, v in checks.items() if not v]

    def validate_for_contract(self) -> list[str]:
        missing = self.validate_for_nda()
        extra = {
            "IBAN": self.iban,
            "SWIFT": self.swift,
            "Receiver Name": self.receiver_name,
            "Rate (USD)": self.rate_usd,
        }
        missing.extend(k for k, v in extra.items() if not v)
        return missing


# ══════════════════════════════════════════════════
#  Color helpers
# ══════════════════════════════════════════════════

_rgb_cache: dict[str, tuple] = {}

def hex_to_rgb(h: str) -> tuple:
    if h in _rgb_cache:
        return _rgb_cache[h]
    raw = h.lstrip("#")
    result = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    _rgb_cache[h] = result
    return result


# Legacy palette constants (kept for backward compat with nda_text/contract_text)
NDA_C = NDA_PALETTE
CONTRACT_C = CONTRACT_PALETTE

BODY_FONT = "Cambria"
HEAD_FONT = "Calibri"
ML = 18.0  # margin left
CW = 174.0  # content width
CT = 17.0  # content top (after header)
CB = 277.0  # content bottom (before footer)

NDA_TERM_YEARS = 5
CONTRACT_END_DATE = "31.12.2026"
TAX_RATE = 0.06

WS_NAME = "Woodenshark LLC"
WS_ADDRESS = "3411 Silverside Road, Suite 104\nWilmington, DE 19810, USA"
WS_ADDRESS_FLAT = "3411 Silverside Road, Suite 104, Rodney Building, Wilmington, DE, 19810"
WS_SWIFT = "CMFGUS33"
WS_ACCOUNT = "822000034828"
WS_BANK = "Wise Inc"


# ══════════════════════════════════════════════════
#  Date / Number helpers
# ══════════════════════════════════════════════════

def fmt_date(d) -> str:
    if d is None:
        return ""
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d).date()
        except ValueError:
            return d
    if isinstance(d, datetime):
        d = d.date()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    return f"{months[d.month - 1]} {d.day}, {d.year}"


def num_words(n) -> str:
    ones = ["", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen",
            "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"]
    n = round(n)
    if n == 0: return "zero"
    if n < 20: return ones[n]
    if n < 100: return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
    if n < 1000: return ones[n // 100] + " hundred" + (" " + num_words(n % 100) if n % 100 else "")
    if n < 1_000_000: return num_words(n // 1000) + " thousand" + (" " + num_words(n % 1000) if n % 1000 else "")
    return str(n)


def _num_word_short(n):
    w = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    return w[n] if 1 <= n <= 10 else str(n)


def set_color(pdf, hx, kind="text"):
    r, g, b = hex_to_rgb(hx)
    if kind == "text": pdf.set_text_color(r, g, b)
    elif kind == "fill": pdf.set_fill_color(r, g, b)
    elif kind == "draw": pdf.set_draw_color(r, g, b)


# ══════════════════════════════════════════════════
#  WsPDF — FPDF subclass with header/footer
# ══════════════════════════════════════════════════

class WsPDF(FPDF):
    def __init__(self, theme: Optional[CompanyTheme] = None, **kw):
        super().__init__(**kw)
        self._is_title_page = True
        self._doc_type = "Document"
        self._theme = theme or CompanyTheme()
        # Header/footer theming (can be overridden per-doc)
        self._header_color = "#1A0000"
        self._accent_color = "#C62828"
        self._header_text_color = "#D4A017"
        self._header_label = "STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED"
        self._company_color = "#8B0000"

    def header(self):
        if self._is_title_page:
            return
        # Watermark (behind content)
        with self.rotation(45, self.w / 2, self.h / 2):
            self.set_font(HEAD_FONT, "B", 42)
            self.set_text_color(245, 245, 245)
            t = self._theme.watermark_text
            self.text(self.w / 2 - self.get_string_width(t) / 2, self.h / 2, t)
        # Header bar
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 15, style="F")
        r, g, b = hex_to_rgb(self._header_color)
        self.set_fill_color(r, g, b)
        self.rect(0, 0, 210, 7, style="F")
        self.set_font(HEAD_FONT, "", 6)
        r, g, b = hex_to_rgb(self._header_text_color)
        self.set_text_color(r, g, b)
        self.set_xy(0, 2)
        self.cell(210, 4, self._header_label, align="C")
        self.set_font(HEAD_FONT, "B", 7)
        r, g, b = hex_to_rgb(self._company_color)
        self.set_text_color(r, g, b)
        self.set_xy(18, 8)
        self.cell(0, 4, self._theme.company_name.upper())
        self.set_font(HEAD_FONT, "", 7)
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
        self.set_fill_color(255, 255, 255)
        self.rect(0, 277, 210, 20, style="F")
        self.set_draw_color(208, 208, 208)
        self.set_line_width(0.15)
        self.line(18, 283, 192, 283)
        self.set_font(HEAD_FONT, "", 7)
        self.set_text_color(107, 107, 107)
        self.set_xy(0, 284)
        self.cell(210, 4, f"{self._doc_type}  |  STRICTLY CONFIDENTIAL  |  Page {{nb}}", align="C")
        r, g, b = hex_to_rgb(self._header_color)
        self.set_fill_color(r, g, b)
        self.rect(0, 289, 210, 8, style="F")
        self.set_font(HEAD_FONT, "", 6)
        r, g, b = hex_to_rgb(self._header_text_color)
        self.set_text_color(r, g, b)
        self.set_xy(0, 291)
        self.cell(210, 4, self._header_label, align="C")


def _make_pdf(employee_id, fonts_dir: Path, theme: Optional[CompanyTheme] = None) -> WsPDF:
    rnd = uuid.uuid4().hex[:8]
    prefix = "".join(c for c in (theme or CompanyTheme()).company_name[:4].upper() if c.isalpha()) or "WS"
    pdf = WsPDF(theme=theme, orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_compression(True)
    pdf.alias_nb_pages()
    pdf.set_encryption(
        owner_password=f"{prefix}-{employee_id}-{rnd}",
        user_password="",
        encryption_method="AES-256",
        permissions=AccessPermission.all(),
    )
    for fam, files in [
        (BODY_FONT, ("cambria.ttf", "cambriab.ttf", "cambriai.ttf", "cambriaz.ttf")),
        (HEAD_FONT, ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf")),
    ]:
        for i, style in enumerate(("", "B", "I", "BI")):
            p = fonts_dir / files[i]
            if p.exists():
                pdf.add_font(fam, style, str(p))
            elif style in ("", "B"):
                raise FileNotFoundError(f"Required font missing: {p}")
    return pdf


def _page_break(pdf, needed=30):
    if pdf.get_y() + needed > CB:
        pdf.add_page()
        pdf.set_y(CT + 2)


def _sec_heading(pdf, title, color):
    _page_break(pdf, 20)
    pdf.ln(6)
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "B", 13)
    set_color(pdf, color)
    pdf.cell(CW, 7, title, new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y()
    set_color(pdf, color, "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 3)


def _body(pdf, text):
    _page_break(pdf)
    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, "#1A1A1A")
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, text, align="J")
    pdf.ln(2)


def _sub(pdf, label, text, accent):
    _page_break(pdf)
    pdf.set_x(ML + 2)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, accent)
    lw = pdf.get_string_width(label + " ")
    pdf.cell(lw, 5, label + " ")
    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, "#1A1A1A")
    pdf.multi_cell(CW - 2 - lw, 5, text, align="J")
    pdf.ln(1)


# ══════════════════════════════════════════════════
#  Bilingual Renderer
# ══════════════════════════════════════════════════

class BilingualRenderer:
    """Renders bilingual (EN + local language) content into PDF.

    Design rules:
    - EN: primary size (11pt body, 13pt heading), dark color
    - Local: -1.5pt from EN, italic, gray (#777–#888)
    - If local_lang is None → EN only
    - Thin separator between sections
    """

    LOCAL_HEADING_COLOR = "#888888"
    LOCAL_BODY_COLOR = "#777777"
    SEPARATOR_COLOR = "#CCCCCC"

    def __init__(self, pdf: WsPDF, palette: dict, local_lang: Optional[str] = None):
        self.pdf = pdf
        self.palette = palette
        self.local_lang = local_lang
        self._accent = palette.get("CRIMSON", palette.get("DARK", "#333333"))
        self._sub_accent = palette.get("RED_ACCENT", palette.get("CYAN_DARK", "#555555"))

    @property
    def has_local(self) -> bool:
        return self.local_lang is not None and self.local_lang != "none"

    def render_section_heading(self, title_en: str, title_local: Optional[str] = None):
        _page_break(self.pdf, 20)
        self.pdf.ln(6)
        self.pdf.set_x(ML)
        self.pdf.set_font(HEAD_FONT, "B", 13)
        set_color(self.pdf, self._accent)
        self.pdf.cell(CW, 7, title_en, new_x="LMARGIN", new_y="NEXT")

        if self.has_local and title_local:
            self.pdf.set_x(ML)
            self.pdf.set_font(HEAD_FONT, "BI", 10)
            set_color(self.pdf, self.LOCAL_HEADING_COLOR)
            self.pdf.cell(CW, 5, title_local, new_x="LMARGIN", new_y="NEXT")

        y = self.pdf.get_y()
        set_color(self.pdf, self._accent, "draw")
        self.pdf.set_line_width(0.4)
        self.pdf.line(ML, y, ML + CW, y)
        self.pdf.set_y(y + 3)

    def render_paragraph(self, text_en: str, text_local: Optional[str] = None):
        _page_break(self.pdf)
        self.pdf.set_font(BODY_FONT, "", 11)
        set_color(self.pdf, "#1A1A1A")
        self.pdf.set_x(ML)
        self.pdf.multi_cell(CW, 5, text_en, align="J")
        self.pdf.ln(1)

        if self.has_local and text_local:
            self.pdf.set_font(BODY_FONT, "I", 9.5)
            set_color(self.pdf, self.LOCAL_BODY_COLOR)
            self.pdf.set_x(ML)
            self.pdf.multi_cell(CW, 4.5, text_local, align="J")
            self.pdf.ln(1)

        self.pdf.ln(1)

    def render_bullet(self, label: str, text_en: str,
                      label_local: Optional[str] = None,
                      text_local: Optional[str] = None):
        _page_break(self.pdf)
        # EN bullet
        self.pdf.set_x(ML + 2)
        self.pdf.set_font(BODY_FONT, "B", 11)
        set_color(self.pdf, self._sub_accent)
        lw = self.pdf.get_string_width(label + " ")
        self.pdf.cell(lw, 5, label + " ")
        self.pdf.set_font(BODY_FONT, "", 11)
        set_color(self.pdf, "#1A1A1A")
        self.pdf.multi_cell(CW - 2 - lw, 5, text_en, align="J")

        # Local bullet
        if self.has_local and text_local:
            local_label = label_local or label
            self.pdf.set_x(ML + 2)
            self.pdf.set_font(BODY_FONT, "BI", 9.5)
            set_color(self.pdf, self._sub_accent)
            llw = self.pdf.get_string_width(local_label + " ")
            self.pdf.cell(llw, 4.5, local_label + " ")
            self.pdf.set_font(BODY_FONT, "I", 9.5)
            set_color(self.pdf, self.LOCAL_BODY_COLOR)
            self.pdf.multi_cell(CW - 2 - llw, 4.5, text_local, align="J")

        self.pdf.ln(1)

    def render_separator(self):
        y = self.pdf.get_y()
        set_color(self.pdf, self.SEPARATOR_COLOR, "draw")
        self.pdf.set_line_width(0.15)
        self.pdf.line(ML, y, ML + CW, y)
        self.pdf.set_y(y + 2)

    def render_section(self, section: SectionData):
        """Render a full section from SectionData."""
        self.render_section_heading(section.title_en, section.title_local)

        local_items = section.content_local or []

        for i, item in enumerate(section.content_en):
            local_item = local_items[i] if i < len(local_items) else None

            if isinstance(item, dict):
                item_type = item.get("type", "paragraph")
                text_en = item.get("text", "")
                text_local = local_item.get("text", "") if isinstance(local_item, dict) else None

                if item_type == "paragraph":
                    self.render_paragraph(text_en, text_local)
                elif item_type == "bullet":
                    label = item.get("label", "")
                    label_local = local_item.get("label") if isinstance(local_item, dict) else None
                    self.render_bullet(label, text_en, label_local, text_local)
                elif item_type == "callout":
                    self._render_callout(text_en, text_local)
            elif isinstance(item, str):
                local_text = local_item if isinstance(local_item, str) else None
                self.render_paragraph(item, local_text)

    def _render_callout(self, text_en: str, text_local: Optional[str] = None):
        """Render a callout box (tinted bg + left border)."""
        _page_break(self.pdf, 20)
        tint = self.palette.get("RED_TINT", self.palette.get("CYAN_TINT", "#F5F5F5"))
        accent = self.palette.get("RED_ACCENT", self.palette.get("CYAN", "#999999"))

        y = self.pdf.get_y()
        set_color(self.pdf, tint, "fill")
        set_color(self.pdf, accent, "draw")
        self.pdf.set_line_width(0.8)
        h = 20 if not (self.has_local and text_local) else 30
        self.pdf.rect(ML, y, CW, h, style="DF")
        set_color(self.pdf, accent, "fill")
        self.pdf.rect(ML, y, 1.2, h, style="F")

        self.pdf.set_xy(ML + 4, y + 3)
        self.pdf.set_font(BODY_FONT, "B", 11)
        set_color(self.pdf, self.palette.get("TEXT_PRIMARY", "#1A1A1A"))
        self.pdf.multi_cell(CW - 8, 5, text_en, align="J")

        if self.has_local and text_local:
            self.pdf.set_x(ML + 4)
            self.pdf.set_font(BODY_FONT, "BI", 9.5)
            set_color(self.pdf, self.LOCAL_BODY_COLOR)
            self.pdf.multi_cell(CW - 8, 4.5, text_local, align="J")

        self.pdf.set_y(y + h + 2)


# ══════════════════════════════════════════════════
#  NDA GENERATOR
# ══════════════════════════════════════════════════

def generate_nda(emp: EmployeeData, fonts_dir: Path,
                 template: Optional[TemplateData] = None) -> tuple:
    """Returns (pdf_bytes, filename). Raises ValueError if required fields missing.

    Args:
        emp: Employee data
        fonts_dir: Path to fonts directory
        template: Optional TemplateData. If None, uses default Woodenshark NDA template.
    """
    missing = emp.validate_for_nda()
    if missing:
        raise ValueError(f"NDA: missing fields — {', '.join(missing)}")

    tmpl = template or default_nda_template()
    theme = tmpl.theme
    C = tmpl.palette or NDA_PALETTE
    pdf = _make_pdf(emp.id, fonts_dir, theme)
    pdf._doc_type = tmpl.doc_title
    pdf._header_color = C.get("HEADER_COLOR", C.get("DARK_RED", "#1A0000"))
    pdf._accent_color = C.get("ACCENT_COLOR", C.get("RED_ACCENT", "#C62828"))
    pdf._header_text_color = C.get("HEADER_TEXT_COLOR", C.get("GOLD_LIGHT", "#D4A017"))
    pdf._header_label = tmpl.header_label
    pdf._company_color = C.get("COMPANY_COLOR", C.get("CRIMSON", "#8B0000"))

    ed = fmt_date(emp.effective_date or emp.agreement_date or date.today())

    # ── Title page ──
    pdf.add_page()
    pdf.set_y(30)
    pdf.set_x(ML)

    # Company name split: first word big, rest accent color
    name_parts = theme.company_name.upper().split(" ", 1)
    pdf.set_font(HEAD_FONT, "B", 32)
    set_color(pdf, C.get("DARK_RED", C.get("NAVY", "#1A0000")))
    w = pdf.get_string_width(name_parts[0])
    pdf.cell(w, 12, name_parts[0])
    if len(name_parts) > 1:
        set_color(pdf, C.get("CRIMSON", C.get("CYAN_DARK", "#8B0000")))
        pdf.cell(0, 12, " " + name_parts[1], new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 12, "", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 2
    set_color(pdf, C.get("RED_ACCENT", C.get("CYAN", "#C62828")), "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 12)

    pdf.set_font(HEAD_FONT, "B", 28)
    set_color(pdf, C.get("DARK_RED", C.get("NAVY", "#1A0000")))
    pdf.cell(0, 10, "NON-DISCLOSURE AGREEMENT", new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 2
    set_color(pdf, C.get("DARK_RED", C.get("NAVY", "#1A0000")), "draw")
    pdf.set_line_width(0.6)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)

    pdf.set_font(HEAD_FONT, "", 14)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 8, tmpl.doc_subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 10)

    def info_row(lbl, val):
        pdf.set_x(ML)
        pdf.set_font(HEAD_FONT, "", 8.5)
        set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(40, 6, lbl)
        pdf.set_font(BODY_FONT, "B", 11)
        set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 6, val, new_x="LMARGIN", new_y="NEXT")

    info_row("EFFECTIVE DATE", ed)
    info_row("DURATION", f"{tmpl.nda_term_years} years")
    y = pdf.get_y() + 2
    set_color(pdf, C["LIGHT_GRAY"], "draw")
    pdf.set_line_width(0.15)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    info_row("DISCLOSING PARTY", theme.company_name)
    info_row("RECEIVING PARTY", emp.full_name_lat)

    pdf.set_y(260)
    pdf.set_font(HEAD_FONT, "", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(32, 6, "CLASSIFICATION: ")
    set_color(pdf, tmpl.classification_bg_color or C.get("DARK_RED", "#1A0000"), "fill")
    set_color(pdf, tmpl.classification_text_color or C.get("GOLD_LIGHT", "#D4A017"))
    pdf.cell(50, 6, tmpl.classification_label, fill=True, align="C")

    # ── Content pages ──
    pdf.add_page()
    pdf.set_y(CT + 2)

    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, f'This Non-Disclosure Agreement (the \u201cAgreement\u201d) is entered into as of {ed} (the \u201cEffective Date\u201d).', align="J")
    pdf.ln(4)

    pdf.set_font(HEAD_FONT, "B", 12)
    set_color(pdf, C.get("CRIMSON", C.get("DARK", "#8B0000")))
    pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Party boxes
    _page_break(pdf, 50)
    bw = (CW - 6) / 2
    ys = pdf.get_y()

    party_bg = C.get("PARTY_BG", C.get("FAFBFC", "#FBF5F5"))
    party_accent = C.get("RED_ACCENT", C.get("CYAN", "#C62828"))
    deep_color = C.get("DEEP_RED", C.get("CYAN_DARK", "#7B1A1A"))

    set_color(pdf, party_bg, "fill")
    set_color(pdf, party_accent, "draw")
    pdf.set_line_width(0.7)
    pdf.rect(ML, ys, bw, 40, style="DF")
    set_color(pdf, party_accent, "fill")
    pdf.rect(ML, ys, 0.8, 40, style="F")
    pdf.set_xy(ML + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw - 8, 4, "DISCLOSING PARTY", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, theme.company_name, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in theme.company_address.split("\n"):
        pdf.cell(bw - 8, 4, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML + 4)

    x2 = ML + bw + 6
    set_color(pdf, party_bg, "fill")
    pdf.rect(x2, ys, bw, 40, style="DF")
    set_color(pdf, party_accent, "fill")
    pdf.rect(x2, ys, 0.8, 40, style="F")
    pdf.set_xy(x2 + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw - 8, 4, "RECEIVING PARTY", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2 + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2 + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in [f"Born: {fmt_date(emp.date_of_birth)}", f"Passport: {emp.passport_number}",
               f"Issued: {fmt_date(emp.passport_issued)}", f"Valid until: {fmt_date(emp.passport_expires)}",
               emp.address]:
        if ln:
            pdf.cell(bw - 8, 4, ln, new_x="LEFT", new_y="NEXT")
            pdf.set_x(x2 + 4)
    pdf.set_y(ys + 44)

    # Recitals
    _sec_heading(pdf, "RECITALS", C.get("CRIMSON", C.get("DARK", "#8B0000")))
    for t in [
        f'WHEREAS, the Company is engaged in the research, development, design, and production of Unmanned Aerial Vehicles (\u201cUAVs\u201d), Radio-Electronic Systems, and related defense and dual-use technologies;',
        f'WHEREAS, the Receiving Party possesses specialized technical expertise and has entered into a Consulting Agreement with the Company dated {ed} to provide engineering and technical services;',
        'WHEREAS, in the course of the engagement, the Parties anticipate that the Company may disclose or provide access to certain proprietary, confidential, and trade secret information to the Receiving Party;',
    ]:
        _body(pdf, t)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, 'NOW, THEREFORE, in consideration of the mutual covenants contained herein, the Parties agree as follows:', align="J")
    pdf.ln(3)

    # Sections — use template sections if provided, else fall back to legacy nda_text
    if tmpl.sections:
        renderer = BilingualRenderer(pdf, C, theme.local_lang)
        for section in sorted(tmpl.sections, key=lambda s: s.sequence):
            renderer.render_section(section)
    else:
        from . import nda_text
        nda_text.render_sections(pdf, ed, C)

    # Signature
    _nda_signature(pdf, emp, C, theme)

    buf = BytesIO()
    pdf.output(buf)
    fname = f"NDA {(emp.full_name_lat or 'Unknown').strip()}.pdf"
    return buf.getvalue(), fname


def _nda_signature(pdf, emp, C, theme: Optional[CompanyTheme] = None):
    if theme is None:
        theme = CompanyTheme()
    _page_break(pdf, 80)
    pdf.ln(6)
    y = pdf.get_y()
    dark_color = C.get("DARK_RED", C.get("NAVY", "#1A0000"))
    accent = C.get("RED_ACCENT", C.get("CYAN", "#C62828"))
    deep_color = C.get("DEEP_RED", C.get("CYAN_DARK", "#7B1A1A"))

    set_color(pdf, dark_color, "draw")
    pdf.set_line_width(0.8)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    pdf.set_font(BODY_FONT, "I", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, "IN WITNESS WHEREOF, the Parties have executed this Non-Disclosure Agreement as of the Effective Date first written above.", align="J")
    pdf.ln(4)
    bw = (CW - 6) / 2
    ys = pdf.get_y()
    # Left — Company
    set_color(pdf, accent, "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, ys, ML + bw, ys)
    pdf.set_xy(ML, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw, 4, theme.company_name.upper(), new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 8)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in theme.company_address.split("\n"):
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.ln(4)
    pdf.set_x(ML)
    set_color(pdf, dark_color)
    pdf.cell(bw, 5, "________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, "Signature", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 8)
    set_color(pdf, C["TEXT_SECONDARY"])
    for f in ["Name: ____________________", "Title: ____________________", "Date: ____________________"]:
        pdf.cell(bw, 4, f, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    # Right — Employee
    x2 = ML + bw + 6
    pdf.set_xy(x2, ys)
    set_color(pdf, accent, "draw")
    pdf.line(x2, ys, x2 + bw, ys)
    pdf.set_xy(x2, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw, 4, "RECEIVING PARTY", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "B", 9)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw, 4, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "", 8)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(bw, 3.5, f"Passport: {emp.passport_number}", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.cell(bw, 3.5, emp.work_email, new_x="LEFT", new_y="NEXT")
    pdf.ln(4)
    pdf.set_x(x2)
    set_color(pdf, dark_color)
    pdf.cell(bw, 5, "________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, "Signature", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "", 8)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(bw, 4, f"Name: {emp.full_name_lat}", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.cell(bw, 4, "Date: ____________________", new_x="LEFT", new_y="NEXT")


# ══════════════════════════════════════════════════
#  CONTRACT GENERATOR
# ══════════════════════════════════════════════════

def generate_contract(emp: EmployeeData, fonts_dir: Path,
                      template: Optional[TemplateData] = None) -> tuple:
    """Returns (pdf_bytes, filename). Raises ValueError if required fields missing.

    Args:
        emp: Employee data
        fonts_dir: Path to fonts directory
        template: Optional TemplateData. If None, uses default Woodenshark Contract template.
    """
    missing = emp.validate_for_contract()
    if missing:
        raise ValueError(f"Contract: missing fields — {', '.join(missing)}")

    tmpl = template or default_contract_template()
    theme = tmpl.theme
    C = tmpl.palette or CONTRACT_PALETTE
    pdf = _make_pdf(emp.id, fonts_dir, theme)
    pdf._doc_type = tmpl.doc_title
    pdf._header_color = C.get("HEADER_COLOR", C.get("NAVY", "#0A0E17"))
    pdf._accent_color = C.get("ACCENT_COLOR", C.get("CYAN", "#00BCD4"))
    pdf._header_text_color = C.get("HEADER_TEXT_COLOR", "#FFFFFF")
    pdf._header_label = tmpl.header_label
    pdf._company_color = C.get("COMPANY_COLOR", C.get("DARK", "#0D1117"))

    ad = fmt_date(emp.agreement_date or date.today())
    ed = fmt_date(emp.effective_date or emp.agreement_date or date.today())

    # ── Title page ──
    pdf.add_page()
    pdf.set_y(30)
    pdf.set_x(ML)

    name_parts = theme.company_name.upper().split(" ", 1)
    pdf.set_font(HEAD_FONT, "B", 32)
    set_color(pdf, C.get("NAVY", C.get("DARK_RED", "#0A0E17")))
    w = pdf.get_string_width(name_parts[0])
    pdf.cell(w, 12, name_parts[0])
    if len(name_parts) > 1:
        set_color(pdf, C.get("CYAN_DARK", C.get("CRIMSON", "#0097A7")))
        pdf.cell(0, 12, " " + name_parts[1], new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 12, "", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 2
    set_color(pdf, C.get("CYAN", C.get("RED_ACCENT", "#00BCD4")), "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 12)

    pdf.set_font(HEAD_FONT, "B", 28)
    set_color(pdf, C.get("NAVY", C.get("DARK_RED", "#0A0E17")))
    pdf.cell(0, 10, "CONSULTING AGREEMENT", new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 2
    set_color(pdf, C.get("NAVY", C.get("DARK_RED", "#0A0E17")), "draw")
    pdf.set_line_width(0.6)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    pdf.set_font(HEAD_FONT, "", 14)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 8, tmpl.doc_subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 10)

    def info_row(lbl, val):
        pdf.set_x(ML)
        pdf.set_font(HEAD_FONT, "", 8.5)
        set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(40, 6, lbl)
        pdf.set_font(BODY_FONT, "B", 11)
        set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 6, val, new_x="LMARGIN", new_y="NEXT")

    info_row("AGREEMENT DATE", ad)
    info_row("EFFECTIVE DATE", ed)
    y = pdf.get_y() + 2
    set_color(pdf, C["LIGHT_GRAY"], "draw")
    pdf.set_line_width(0.15)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    info_row("PARTY A (CLIENT)", theme.company_name)
    info_row("PARTY B (CONSULTANT)", emp.full_name_lat)

    pdf.set_y(260)
    pdf.set_font(HEAD_FONT, "", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(32, 6, "CLASSIFICATION: ")
    set_color(pdf, tmpl.classification_bg_color or C.get("NAVY", "#0A0E17"), "fill")
    r, g, b = hex_to_rgb(tmpl.classification_text_color or "#FFFFFF")
    pdf.set_text_color(r, g, b)
    pdf.cell(40, 6, tmpl.classification_label, fill=True, align="C")

    # ── Content pages ──
    pdf.add_page()
    pdf.set_y(CT + 2)

    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, f'THIS CONSULTING AGREEMENT (the \u201cAgreement\u201d) dated {ad}', align="J")
    pdf.ln(4)
    pdf.set_font(HEAD_FONT, "B", 12)
    set_color(pdf, C.get("DARK", C.get("CRIMSON", "#0D1117")))
    pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Party boxes
    _page_break(pdf, 40)
    bw = (CW - 6) / 2
    ys = pdf.get_y()
    party_bg = C.get("FAFBFC", C.get("PARTY_BG", "#FAFBFC"))
    party_accent = C.get("CYAN", C.get("RED_ACCENT", "#00BCD4"))
    deep_color = C.get("CYAN_DARK", C.get("DEEP_RED", "#0097A7"))

    set_color(pdf, party_bg, "fill")
    set_color(pdf, party_accent, "draw")
    pdf.set_line_width(0.5)
    pdf.rect(ML, ys, bw, 32, style="DF")
    set_color(pdf, party_accent, "fill")
    pdf.rect(ML, ys, 0.8, 32, style="F")
    pdf.set_xy(ML + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw - 8, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, theme.company_name, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in theme.company_address.split("\n"):
        pdf.cell(bw - 8, 4, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "I", 10)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw - 8, 4, '(the \u201cClient\u201d)', new_x="LEFT", new_y="NEXT")

    x2 = ML + bw + 6
    set_color(pdf, party_bg, "fill")
    set_color(pdf, party_accent, "draw")
    pdf.rect(x2, ys, bw, 32, style="DF")
    set_color(pdf, party_accent, "fill")
    pdf.rect(x2, ys, 0.8, 32, style="F")
    pdf.set_xy(x2 + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw - 8, 4, "CONSULTANT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2 + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2 + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(bw - 8, 4, emp.address, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2 + 4)
    pdf.set_font(BODY_FONT, "I", 10)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw - 8, 4, '(the \u201cConsultant\u201d)', new_x="LEFT", new_y="NEXT")
    pdf.set_y(ys + 36)

    # Background + sections — use template sections if provided, else fall back to legacy
    if tmpl.sections:
        renderer = BilingualRenderer(pdf, C, theme.local_lang)
        for section in sorted(tmpl.sections, key=lambda s: s.sequence):
            renderer.render_section(section)
    else:
        from . import contract_text
        contract_text.render_sections(pdf, emp, ad, ed, C)

    # Signature
    _contract_signature(pdf, emp, ed, C, theme)

    buf = BytesIO()
    pdf.output(buf)
    fname = f"Consulting Agreement {(emp.full_name_lat or 'Unknown').strip()}.pdf"
    return buf.getvalue(), fname


def _contract_signature(pdf, emp, ed, C, theme: Optional[CompanyTheme] = None):
    if theme is None:
        theme = CompanyTheme()
    _page_break(pdf, 80)
    pdf.ln(6)
    y = pdf.get_y()
    dark_color = C.get("NAVY", C.get("DARK_RED", "#0A0E17"))
    accent = C.get("CYAN", C.get("RED_ACCENT", "#00BCD4"))
    deep_color = C.get("CYAN_DARK", C.get("DEEP_RED", "#0097A7"))

    set_color(pdf, dark_color, "draw")
    pdf.set_line_width(0.8)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    pdf.set_font(BODY_FONT, "I", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, f"IN WITNESS WHEREOF the Parties have duly affixed their signatures under hand and seal on {ed}.", align="J")
    pdf.ln(4)
    bw = (CW - 6) / 2
    ys = pdf.get_y()
    # Client
    set_color(pdf, accent, "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, ys, ML + bw, ys)
    pdf.set_xy(ML, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw, 5, theme.company_name, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in theme.company_address.split("\n"):
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 5, "Bank account:", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in [f"SWIFT: {theme.bank_swift}", f"Account: {theme.bank_account}", theme.bank_name]:
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.ln(3)
    pdf.set_x(ML)
    set_color(pdf, dark_color)
    pdf.cell(bw, 5, "____________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, "Signature", new_x="LEFT", new_y="NEXT")
    # Consultant
    x2 = ML + bw + 6
    pdf.set_xy(x2, ys)
    set_color(pdf, accent, "draw")
    pdf.line(x2, ys, x2 + bw, ys)
    pdf.set_xy(x2, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, deep_color)
    pdf.cell(bw, 4, "CONSULTANT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw, 5, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(bw, 3.5, emp.address, new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 5, "Bank account:", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in [f"IBAN: {emp.iban}", f"SWIFT/BIC: {emp.swift}", f"Receiver: {emp.receiver_name}"]:
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
    pdf.ln(3)
    pdf.set_x(x2)
    set_color(pdf, dark_color)
    pdf.cell(bw, 5, "____________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
