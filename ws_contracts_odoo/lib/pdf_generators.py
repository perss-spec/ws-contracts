"""
Standalone PDF generators for Odoo module.
Combines models + base + nda + contract from ws_contracts package.
No dependency on ws_contracts — everything self-contained.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from fpdf import FPDF
from fpdf.encryption import AccessPermission


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


NDA_C = {
    "DARK_RED": "#1A0000", "CRIMSON": "#8B0000", "RED_ACCENT": "#C62828",
    "DEEP_RED": "#7B1A1A", "GOLD_LIGHT": "#D4A017",
    "TEXT_PRIMARY": "#1A1A1A", "TEXT_SECONDARY": "#4A4A4A",
    "TEXT_MUTED": "#6B6B6B", "LIGHT_GRAY": "#D0D0D0",
    "RED_TINT": "#FDF2F2", "WHITE": "#FFFFFF", "PARTY_BG": "#FBF5F5",
}

CONTRACT_C = {
    "NAVY": "#0A0E17", "DARK": "#0D1117", "CYAN": "#00BCD4",
    "CYAN_DARK": "#0097A7", "TEXT_PRIMARY": "#1A1A1A",
    "TEXT_SECONDARY": "#4A4A4A", "TEXT_MUTED": "#6B6B6B",
    "LIGHT_GRAY": "#D0D0D0", "CYAN_TINT": "#E8F5F7",
    "WHITE": "#FFFFFF", "FAFBFC": "#FAFBFC",
}

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
    def __init__(self, **kw):
        super().__init__(**kw)
        self._is_title_page = True
        self._doc_type = "Document"
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
            t = "WOODENSHARK LLC CONFIDENTIAL"
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
        self.cell(0, 4, "WOODENSHARK LLC")
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


def _make_pdf(employee_id, fonts_dir: Path) -> WsPDF:
    rnd = uuid.uuid4().hex[:8]
    pdf = WsPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_compression(True)
    pdf.alias_nb_pages()
    pdf.set_encryption(
        owner_password=f"WS-{employee_id}-{rnd}",
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
#  NDA GENERATOR
# ══════════════════════════════════════════════════

# Section texts inlined to keep module self-contained
# (imported from nda_sections.py / contract_sections.py of ws_contracts)

def generate_nda(emp: EmployeeData, fonts_dir: Path) -> tuple:
    """Returns (pdf_bytes, filename). Raises ValueError if required fields missing."""
    missing = emp.validate_for_nda()
    if missing:
        raise ValueError(f"NDA: missing fields — {', '.join(missing)}")
    C = NDA_C
    pdf = _make_pdf(emp.id, fonts_dir)
    pdf._doc_type = "Non-Disclosure Agreement"
    pdf._header_color = C["DARK_RED"]
    pdf._accent_color = C["RED_ACCENT"]
    pdf._header_text_color = C["GOLD_LIGHT"]
    pdf._company_color = C["CRIMSON"]

    ed = fmt_date(emp.effective_date or emp.agreement_date or date.today())

    # ── Title page ──
    pdf.add_page()
    pdf.set_y(30)
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "B", 32)
    set_color(pdf, C["DARK_RED"])
    w = pdf.get_string_width("WOODENSHARK")
    pdf.cell(w, 12, "WOODENSHARK")
    set_color(pdf, C["CRIMSON"])
    pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 2
    set_color(pdf, C["RED_ACCENT"], "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 12)

    pdf.set_font(HEAD_FONT, "B", 28)
    set_color(pdf, C["DARK_RED"])
    pdf.cell(0, 10, "NON-DISCLOSURE AGREEMENT", new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 2
    set_color(pdf, C["DARK_RED"], "draw")
    pdf.set_line_width(0.6)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)

    pdf.set_font(HEAD_FONT, "", 14)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 8, "Proprietary & Restricted Information Protection", new_x="LMARGIN", new_y="NEXT")
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
    info_row("DURATION", f"{NDA_TERM_YEARS} years")
    y = pdf.get_y() + 2
    set_color(pdf, C["LIGHT_GRAY"], "draw")
    pdf.set_line_width(0.15)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    info_row("DISCLOSING PARTY", WS_NAME)
    info_row("RECEIVING PARTY", emp.full_name_lat)

    pdf.set_y(260)
    pdf.set_font(HEAD_FONT, "", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(32, 6, "CLASSIFICATION: ")
    set_color(pdf, C["DARK_RED"], "fill")
    set_color(pdf, C["GOLD_LIGHT"])
    pdf.cell(50, 6, "STRICTLY CONFIDENTIAL", fill=True, align="C")

    # ── Content pages ──
    pdf.add_page()
    pdf.set_y(CT + 2)

    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, f'This Non-Disclosure Agreement (the \u201cAgreement\u201d) is entered into as of {ed} (the \u201cEffective Date\u201d).', align="J")
    pdf.ln(4)

    pdf.set_font(HEAD_FONT, "B", 12)
    set_color(pdf, C["CRIMSON"])
    pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Party boxes
    _page_break(pdf, 50)
    bw = (CW - 6) / 2
    ys = pdf.get_y()

    set_color(pdf, C["PARTY_BG"], "fill")
    set_color(pdf, C["RED_ACCENT"], "draw")
    pdf.set_line_width(0.7)
    pdf.rect(ML, ys, bw, 40, style="DF")
    set_color(pdf, C["RED_ACCENT"], "fill")
    pdf.rect(ML, ys, 0.8, 40, style="F")
    pdf.set_xy(ML + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["DEEP_RED"])
    pdf.cell(bw - 8, 4, "DISCLOSING PARTY", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, WS_NAME, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in WS_ADDRESS.split("\n"):
        pdf.cell(bw - 8, 4, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML + 4)

    x2 = ML + bw + 6
    set_color(pdf, C["PARTY_BG"], "fill")
    pdf.rect(x2, ys, bw, 40, style="DF")
    set_color(pdf, C["RED_ACCENT"], "fill")
    pdf.rect(x2, ys, 0.8, 40, style="F")
    pdf.set_xy(x2 + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["DEEP_RED"])
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
    _sec_heading(pdf, "RECITALS", C["CRIMSON"])
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

    # Sections 1-12 (abbreviated for brevity — full text from nda_sections)
    from . import nda_text
    nda_text.render_sections(pdf, ed, C)

    # Signature
    _nda_signature(pdf, emp, C)

    buf = BytesIO()
    pdf.output(buf)
    fname = f"NDA {(emp.full_name_lat or 'Unknown').strip()}.pdf"
    return buf.getvalue(), fname


def _nda_signature(pdf, emp, C):
    _page_break(pdf, 80)
    pdf.ln(6)
    y = pdf.get_y()
    set_color(pdf, C["DARK_RED"], "draw")
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
    # Left — WS
    set_color(pdf, C["RED_ACCENT"], "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, ys, ML + bw, ys)
    pdf.set_xy(ML, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["DEEP_RED"])
    pdf.cell(bw, 4, "WOODENSHARK LLC", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 8)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in ["3411 Silverside Road", "Suite 104, Wilmington", "DE 19810, USA"]:
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.ln(4)
    pdf.set_x(ML)
    set_color(pdf, C["DARK_RED"])
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
    set_color(pdf, C["RED_ACCENT"], "draw")
    pdf.line(x2, ys, x2 + bw, ys)
    pdf.set_xy(x2, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["DEEP_RED"])
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
    set_color(pdf, C["DARK_RED"])
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

def generate_contract(emp: EmployeeData, fonts_dir: Path) -> tuple:
    """Returns (pdf_bytes, filename). Raises ValueError if required fields missing."""
    missing = emp.validate_for_contract()
    if missing:
        raise ValueError(f"Contract: missing fields — {', '.join(missing)}")
    C = CONTRACT_C
    pdf = _make_pdf(emp.id, fonts_dir)
    pdf._doc_type = "Consulting Agreement"
    pdf._header_color = C["NAVY"]
    pdf._accent_color = C["CYAN"]
    pdf._header_text_color = "#FFFFFF"
    pdf._header_label = "CONFIDENTIAL  \u2014  WOODENSHARK LLC PROPRIETARY"
    pdf._company_color = C["DARK"]

    ad = fmt_date(emp.agreement_date or date.today())
    ed = fmt_date(emp.effective_date or emp.agreement_date or date.today())

    # ── Title page ──
    pdf.add_page()
    pdf.set_y(30)
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "B", 32)
    set_color(pdf, C["NAVY"])
    w = pdf.get_string_width("WOODENSHARK")
    pdf.cell(w, 12, "WOODENSHARK")
    set_color(pdf, C["CYAN_DARK"])
    pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 2
    set_color(pdf, C["CYAN"], "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 12)

    pdf.set_font(HEAD_FONT, "B", 28)
    set_color(pdf, C["NAVY"])
    pdf.cell(0, 10, "CONSULTING AGREEMENT", new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 2
    set_color(pdf, C["NAVY"], "draw")
    pdf.set_line_width(0.6)
    pdf.line(ML, y, ML + CW, y)
    pdf.set_y(y + 4)
    pdf.set_font(HEAD_FONT, "", 14)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 8, "Professional Services & Technical Consulting", new_x="LMARGIN", new_y="NEXT")
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
    info_row("PARTY A (CLIENT)", WS_NAME)
    info_row("PARTY B (CONSULTANT)", emp.full_name_lat)

    pdf.set_y(260)
    pdf.set_font(HEAD_FONT, "", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(32, 6, "CLASSIFICATION: ")
    set_color(pdf, C["NAVY"], "fill")
    pdf.set_text_color(255, 255, 255)
    pdf.cell(40, 6, "CONFIDENTIAL", fill=True, align="C")

    # ── Content pages ──
    pdf.add_page()
    pdf.set_y(CT + 2)

    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, f'THIS CONSULTING AGREEMENT (the \u201cAgreement\u201d) dated {ad}', align="J")
    pdf.ln(4)
    pdf.set_font(HEAD_FONT, "B", 12)
    set_color(pdf, C["DARK"])
    pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Party boxes
    _page_break(pdf, 40)
    bw = (CW - 6) / 2
    ys = pdf.get_y()
    set_color(pdf, C["FAFBFC"], "fill")
    set_color(pdf, C["CYAN"], "draw")
    pdf.set_line_width(0.5)
    pdf.rect(ML, ys, bw, 32, style="DF")
    set_color(pdf, C["CYAN"], "fill")
    pdf.rect(ML, ys, 0.8, 32, style="F")
    pdf.set_xy(ML + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["CYAN_DARK"])
    pdf.cell(bw - 8, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw - 8, 5, WS_NAME, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "", 10)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in WS_ADDRESS.split("\n"):
        pdf.cell(bw - 8, 4, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML + 4)
    pdf.set_font(BODY_FONT, "I", 10)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw - 8, 4, '(the \u201cClient\u201d)', new_x="LEFT", new_y="NEXT")

    x2 = ML + bw + 6
    set_color(pdf, C["FAFBFC"], "fill")
    set_color(pdf, C["CYAN"], "draw")
    pdf.rect(x2, ys, bw, 32, style="DF")
    set_color(pdf, C["CYAN"], "fill")
    pdf.rect(x2, ys, 0.8, 32, style="F")
    pdf.set_xy(x2 + 4, ys + 3)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["CYAN_DARK"])
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

    # Background + sections
    from . import contract_text
    contract_text.render_sections(pdf, emp, ad, ed, C)

    # Signature
    _contract_signature(pdf, emp, ed, C)

    buf = BytesIO()
    pdf.output(buf)
    fname = f"Consulting Agreement {(emp.full_name_lat or 'Unknown').strip()}.pdf"
    return buf.getvalue(), fname


def _contract_signature(pdf, emp, ed, C):
    _page_break(pdf, 80)
    pdf.ln(6)
    y = pdf.get_y()
    set_color(pdf, C["NAVY"], "draw")
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
    set_color(pdf, C["CYAN"], "draw")
    pdf.set_line_width(0.4)
    pdf.line(ML, ys, ML + bw, ys)
    pdf.set_xy(ML, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["CYAN_DARK"])
    pdf.cell(bw, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(bw, 5, WS_NAME, new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in WS_ADDRESS.split("\n"):
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 5, "Bank account:", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(BODY_FONT, "", 9)
    set_color(pdf, C["TEXT_SECONDARY"])
    for ln in [f"SWIFT: {WS_SWIFT}", f"Account: {WS_ACCOUNT}", WS_BANK]:
        pdf.cell(bw, 3.5, ln, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ML)
    pdf.ln(3)
    pdf.set_x(ML)
    set_color(pdf, C["NAVY"])
    pdf.cell(bw, 5, "____________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(ML)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, "Signature", new_x="LEFT", new_y="NEXT")
    # Consultant
    x2 = ML + bw + 6
    pdf.set_xy(x2, ys)
    set_color(pdf, C["CYAN"], "draw")
    pdf.line(x2, ys, x2 + bw, ys)
    pdf.set_xy(x2, ys + 2)
    pdf.set_font(HEAD_FONT, "B", 9)
    set_color(pdf, C["CYAN_DARK"])
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
    set_color(pdf, C["NAVY"])
    pdf.cell(bw, 5, "____________________________", new_x="LEFT", new_y="NEXT")
    pdf.set_x(x2)
    pdf.set_font(HEAD_FONT, "", 8)
    set_color(pdf, C["TEXT_MUTED"])
    pdf.cell(bw, 4, emp.full_name_lat, new_x="LEFT", new_y="NEXT")
