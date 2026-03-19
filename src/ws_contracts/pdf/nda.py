"""NDA PDF generator — Non-Disclosure Agreement."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from fpdf import FPDF

from ..models import CompanyInfo, EmployeeData
from . import nda_sections as S
from .base import BasePdfGenerator
from .styles import DIMS, FONTS, NDA_PALETTE as C, NDA_TERM_YEARS, hex_to_rgb


class NdaPdfGenerator(BasePdfGenerator):

    def __init__(self, fonts_dir: Path | str):
        super().__init__(fonts_dir)
        self.company = CompanyInfo()

    def generate(self, emp: EmployeeData) -> bytes:
        pdf = self._create_pdf(emp.id)
        effective_date = self.format_date(emp.effective_date or emp.agreement_date or date.today())

        self._title_page(pdf, emp, effective_date)
        self._content_pages(pdf, emp, effective_date)

        # Add watermark + header/footer to all pages except page 1
        total = pdf.pages_count
        for i in range(1, total + 1):
            pdf.page = i
            if i > 1:
                self._draw_header(pdf, i, total)
                self._draw_footer(pdf, i, total)
            self._draw_watermark(pdf)

        buf = BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def get_filename(self, emp: EmployeeData) -> str:
        name = (emp.full_name_lat or "Unknown").strip()
        return f"NDA {name}.pdf"

    # ── Title Page ──

    def _title_page(self, pdf: FPDF, emp: EmployeeData, effective_date: str) -> None:
        pdf.add_page()

        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]

        # Brand
        pdf.set_y(30)
        pdf.set_font(FONTS["HEADING"], "B", 32)
        self._set_color(pdf, C["DARK_RED"])
        pdf.cell(0, 12, "WOODENSHARK", new_x="LEFT", new_y="NEXT")
        pdf.set_font(FONTS["HEADING"], "B", 32)
        self._set_color(pdf, C["CRIMSON"])
        pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

        # Red accent line
        pdf.set_y(pdf.get_y() - 20)
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "B", 32)
        ws_w = pdf.get_string_width("WOODENSHARK")
        pdf.set_x(ml + ws_w)
        self._set_color(pdf, C["CRIMSON"])
        pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

        # Reset — draw brand properly
        pdf.set_y(30)
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "B", 32)
        self._set_color(pdf, C["DARK_RED"])
        ws_w = pdf.get_string_width("WOODENSHARK")
        pdf.cell(ws_w, 12, "WOODENSHARK")
        self._set_color(pdf, C["CRIMSON"])
        pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

        # Red line
        y = pdf.get_y() + 2
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.set_line_width(0.4)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 12)

        # Document title
        pdf.set_font(FONTS["HEADING"], "B", 28)
        self._set_color(pdf, C["DARK_RED"])
        pdf.cell(0, 10, "NON-DISCLOSURE AGREEMENT", new_x="LMARGIN", new_y="NEXT")

        # Dark red line
        y = pdf.get_y() + 2
        self._set_color(pdf, C["DARK_RED"], "draw")
        pdf.set_line_width(0.6)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)

        # Subtitle
        pdf.set_font(FONTS["HEADING"], "", 14)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(0, 8, "Proprietary & Restricted Information Protection", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() + 10)

        # Info table
        self._info_row(pdf, "EFFECTIVE DATE", effective_date)
        self._info_row(pdf, "DURATION", f"{NDA_TERM_YEARS} years")
        # Separator
        y = pdf.get_y() + 2
        self._set_color(pdf, C["LIGHT_GRAY"], "draw")
        pdf.set_line_width(0.15)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)
        self._info_row(pdf, "DISCLOSING PARTY", self.company.name)
        self._info_row(pdf, "RECEIVING PARTY", emp.full_name_lat or "")

        # Classification badge at bottom
        pdf.set_y(260)
        pdf.set_font(FONTS["HEADING"], "", 9)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(32, 6, "CLASSIFICATION: ")
        self._set_color(pdf, C["DARK_RED"], "fill")
        self._set_color(pdf, C["GOLD_LIGHT"])
        pdf.cell(50, 6, "STRICTLY CONFIDENTIAL", fill=True, align="C")

    def _info_row(self, pdf: FPDF, label: str, value: str) -> None:
        ml = DIMS["MARGIN_LEFT"]
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "", 8.5)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(40, 6, label)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    # ── Content Pages ──

    def _content_pages(self, pdf: FPDF, emp: EmployeeData, effective_date: str) -> None:
        pdf.add_page()
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        pdf.set_y(DIMS["CONTENT_TOP"] + 2)

        # Preamble
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, f"This Non-Disclosure Agreement (the \u201cAgreement\u201d) is entered into as of {effective_date} (the \u201cEffective Date\u201d).", align="J")
        pdf.ln(4)

        # BETWEEN
        pdf.set_font(FONTS["HEADING"], "B", 12)
        self._set_color(pdf, C["CRIMSON"])
        pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Party boxes
        self._party_boxes(pdf, emp, effective_date)

        # Recitals
        self._section_heading(pdf, "RECITALS")
        for text in S.RECITALS:
            text = text.replace("{effective_date}", effective_date)
            self._body_para(pdf, text)

        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, S.RECITALS_CONCLUSION, align="J")
        pdf.ln(3)

        # Section 1: Definitions
        self._section_heading(pdf, "1. DEFINITIONS")
        for num, text in S.DEFINITIONS:
            self._sub_para(pdf, num, text)

        # Section 2: Confidential Information
        self._section_heading(pdf, "2. CONFIDENTIAL INFORMATION")
        self._body_para(pdf, S.CONFIDENTIAL_INFO_INTRO)
        for num, text in S.CONFIDENTIAL_INFO_ITEMS:
            self._sub_para(pdf, num, text)
        self._body_para(pdf, S.CONFIDENTIAL_INFO_CLOSING)

        # Section 3: Obligations
        self._section_heading(pdf, "3. OBLIGATIONS OF RECEIVING PARTY")
        for num, text in S.OBLIGATIONS:
            self._sub_para(pdf, num, text)

        # Section 4: Exclusions
        self._section_heading(pdf, "4. EXCLUSIONS FROM CONFIDENTIAL INFORMATION")
        self._body_para(pdf, S.EXCLUSIONS_INTRO)
        for num, text in S.EXCLUSIONS_ITEMS:
            self._sub_para(pdf, num, text)

        # Section 5: Term
        self._section_heading(pdf, "5. TERM AND TERMINATION")
        for num, text in S.term_paragraphs(NDA_TERM_YEARS):
            self._sub_para(pdf, num, text)

        # Section 6: Return of Materials
        self._section_heading(pdf, "6. RETURN OF MATERIALS")
        for num, text in S.RETURN_MATERIALS:
            self._sub_para(pdf, num, text)

        # Section 7: Remedies
        self._section_heading(pdf, "7. REMEDIES")
        self._callout_box(pdf, S.REMEDIES_CALLOUT)
        for num, text in S.REMEDIES:
            self._sub_para(pdf, num, text)

        # Section 8: Non-Solicitation
        self._section_heading(pdf, "8. NON-SOLICITATION")
        self._body_para(pdf, S.NON_SOLICITATION)

        # Section 9: IP
        self._section_heading(pdf, "9. INTELLECTUAL PROPERTY")
        for num, text in S.INTELLECTUAL_PROPERTY:
            self._sub_para(pdf, num, text)

        # Section 10: Governing Law
        self._section_heading(pdf, "10. GOVERNING LAW AND JURISDICTION")
        for num, text in S.GOVERNING_LAW:
            self._sub_para(pdf, num, text)

        # Section 11: General Provisions
        self._section_heading(pdf, "11. GENERAL PROVISIONS")
        for num, text in S.GENERAL_PROVISIONS:
            self._sub_para(pdf, num, text)

        # Section 12: Entire Agreement
        self._section_heading(pdf, "12. ENTIRE AGREEMENT")
        self._body_para(pdf, S.ENTIRE_AGREEMENT_TEMPLATE.format(effective_date=effective_date))

        # Signature block
        self._signature_block(pdf, emp, effective_date)

    # ── Rendering helpers ──

    def _check_page_break(self, pdf: FPDF, needed: float = 30) -> None:
        if pdf.get_y() + needed > DIMS["CONTENT_BOTTOM"]:
            pdf.add_page()
            pdf.set_y(DIMS["CONTENT_TOP"] + 2)

    def _section_heading(self, pdf: FPDF, title: str) -> None:
        self._check_page_break(pdf, 20)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        pdf.ln(6)
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "B", 13)
        self._set_color(pdf, C["CRIMSON"])
        pdf.cell(cw, 7, title, new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.set_line_width(0.4)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 3)

    def _body_para(self, pdf: FPDF, text: str) -> None:
        self._check_page_break(pdf)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, text, align="J")
        pdf.ln(2)

    def _sub_para(self, pdf: FPDF, label: str, text: str) -> None:
        self._check_page_break(pdf)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        pdf.set_x(ml + 2)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["RED_ACCENT"])
        lw = pdf.get_string_width(label + " ")
        pdf.cell(lw, 5, label + " ")
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.multi_cell(cw - 2 - lw, 5, text, align="J")
        pdf.ln(1)

    def _callout_box(self, pdf: FPDF, text: str) -> None:
        self._check_page_break(pdf, 20)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        y = pdf.get_y()
        # Background
        self._set_color(pdf, C["RED_TINT"], "fill")
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.set_line_width(0.8)
        pdf.rect(ml, y, cw, 20, style="DF")
        # Left accent
        self._set_color(pdf, C["RED_ACCENT"], "fill")
        pdf.rect(ml, y, 1.2, 20, style="F")
        pdf.set_xy(ml + 4, y + 3)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.multi_cell(cw - 8, 5, text, align="J")
        pdf.set_y(y + 22)

    def _party_boxes(self, pdf: FPDF, emp: EmployeeData, effective_date: str) -> None:
        self._check_page_break(pdf, 50)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        box_w = (cw - 6) / 2
        y_start = pdf.get_y()

        # Disclosing Party
        self._set_color(pdf, C["PARTY_BG"], "fill")
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.set_line_width(0.7)
        pdf.rect(ml, y_start, box_w, 40, style="DF")
        self._set_color(pdf, C["RED_ACCENT"], "fill")
        pdf.rect(ml, y_start, 0.8, 40, style="F")

        pdf.set_xy(ml + 4, y_start + 3)
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["DEEP_RED"])
        pdf.cell(0, 4, "DISCLOSING PARTY", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml + 4)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 5, self.company.name, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml + 4)
        pdf.set_font(FONTS["BODY"], "", 10)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        for line in self.company.address.split("\n"):
            pdf.cell(0, 4, line, new_x="LEFT", new_y="NEXT")
            pdf.set_x(ml + 4)

        # Receiving Party
        x2 = ml + box_w + 6
        self._set_color(pdf, C["PARTY_BG"], "fill")
        pdf.rect(x2, y_start, box_w, 40, style="DF")
        self._set_color(pdf, C["RED_ACCENT"], "fill")
        pdf.rect(x2, y_start, 0.8, 40, style="F")

        pdf.set_xy(x2 + 4, y_start + 3)
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["DEEP_RED"])
        pdf.cell(0, 4, "RECEIVING PARTY", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2 + 4)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 5, emp.full_name_lat or "", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2 + 4)
        pdf.set_font(FONTS["BODY"], "", 10)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        details = [
            f"Born: {self.format_date(emp.date_of_birth)}",
            f"Passport: {emp.passport_number}",
            f"Issued: {self.format_date(emp.passport_issued)}",
            f"Valid until: {self.format_date(emp.passport_expires)}",
            emp.address or "",
        ]
        for line in details:
            if line:
                pdf.cell(0, 4, line, new_x="LEFT", new_y="NEXT")
                pdf.set_x(x2 + 4)

        pdf.set_y(y_start + 44)

    def _signature_block(self, pdf: FPDF, emp: EmployeeData, effective_date: str) -> None:
        self._check_page_break(pdf, 80)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]

        # Thick line
        pdf.ln(6)
        y = pdf.get_y()
        self._set_color(pdf, C["DARK_RED"], "draw")
        pdf.set_line_width(0.8)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)

        # Witness
        pdf.set_font(FONTS["BODY"], "I", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, f"IN WITNESS WHEREOF, the Parties have executed this Non-Disclosure Agreement as of the Effective Date first written above.", align="J")
        pdf.ln(4)

        box_w = (cw - 6) / 2
        y_start = pdf.get_y()

        # WS signature
        y = y_start
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.set_line_width(0.4)
        pdf.line(ml, y, ml + box_w, y)
        pdf.set_xy(ml, y + 2)

        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["DEEP_RED"])
        pdf.cell(box_w, 4, "WOODENSHARK LLC", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["BODY"], "", 8)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        for line in ["3411 Silverside Road", "Suite 104, Wilmington", "DE 19810, USA"]:
            pdf.cell(box_w, 3.5, line, new_x="LEFT", new_y="NEXT")
            pdf.set_x(ml)
        pdf.ln(4)
        pdf.set_x(ml)
        self._set_color(pdf, C["DARK_RED"])
        pdf.cell(box_w, 5, "________________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "", 8)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 4, "Signature", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["BODY"], "", 8)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 4, "Name: ____________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.cell(box_w, 4, "Title: ____________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.cell(box_w, 4, "Date: ____________________", new_x="LEFT", new_y="NEXT")

        # Receiving party signature
        x2 = ml + box_w + 6
        pdf.set_xy(x2, y_start)
        self._set_color(pdf, C["RED_ACCENT"], "draw")
        pdf.line(x2, y_start, x2 + box_w, y_start)
        pdf.set_xy(x2, y_start + 2)

        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["DEEP_RED"])
        pdf.cell(box_w, 4, "RECEIVING PARTY", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "B", 9)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(box_w, 4, emp.full_name_lat or "", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "", 8)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 3.5, f"Passport: {emp.passport_number}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.cell(box_w, 3.5, emp.work_email or "", new_x="LEFT", new_y="NEXT")
        pdf.ln(4)
        pdf.set_x(x2)
        self._set_color(pdf, C["DARK_RED"])
        pdf.cell(box_w, 5, "________________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["HEADING"], "", 8)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 4, "Signature", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "", 8)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 4, f"Name: {emp.full_name_lat or ''}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.cell(box_w, 4, "Date: ____________________", new_x="LEFT", new_y="NEXT")

    # ── Header / Footer (pages 2+) ──

    def _draw_header(self, pdf: FPDF, page: int, total: int) -> None:
        # White background
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, 210, 15, style="F")

        # Dark red bar
        r, g, b = hex_to_rgb(C["DARK_RED"])
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, 210, 7, style="F")
        pdf.set_font(FONTS["HEADING"], "", 6)
        r, g, b = hex_to_rgb(C["GOLD_LIGHT"])
        pdf.set_text_color(r, g, b)
        pdf.set_xy(0, 2)
        pdf.cell(210, 4, "STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED", align="C")

        # Company line
        pdf.set_font(FONTS["HEADING"], "B", 7)
        r, g, b = hex_to_rgb(C["CRIMSON"])
        pdf.set_text_color(r, g, b)
        pdf.set_xy(18, 8)
        pdf.cell(0, 4, "WOODENSHARK LLC")
        pdf.set_font(FONTS["HEADING"], "", 7)
        r, g, b = hex_to_rgb(C["TEXT_MUTED"])
        pdf.set_text_color(r, g, b)
        pdf.set_xy(0, 8)
        pdf.cell(192, 4, "Non-Disclosure Agreement", align="R")

        # Red line
        r, g, b = hex_to_rgb(C["RED_ACCENT"])
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.4)
        pdf.line(18, 13, 192, 13)

    def _draw_footer(self, pdf: FPDF, page: int, total: int) -> None:
        # White background
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 277, 210, 20, style="F")

        # Gray line
        pdf.set_draw_color(208, 208, 208)
        pdf.set_line_width(0.15)
        pdf.line(18, 283, 192, 283)

        # Page info
        pdf.set_font(FONTS["HEADING"], "", 7)
        pdf.set_text_color(107, 107, 107)
        pdf.set_xy(0, 284)
        pdf.cell(210, 4, f"Non-Disclosure Agreement  |  STRICTLY CONFIDENTIAL  |  Page {page} of {total}", align="C")

        # Dark red bar
        r, g, b = hex_to_rgb(C["DARK_RED"])
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 289, 210, 8, style="F")
        pdf.set_font(FONTS["HEADING"], "", 6)
        r, g, b = hex_to_rgb(C["GOLD_LIGHT"])
        pdf.set_text_color(r, g, b)
        pdf.set_xy(0, 291)
        pdf.cell(210, 4, "STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED", align="C")
