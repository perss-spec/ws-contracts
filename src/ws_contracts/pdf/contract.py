"""Contract PDF generator — Consulting Agreement."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from fpdf import FPDF

from ..models import CompanyInfo, EmployeeData
from . import contract_sections as S
from .base import BasePdfGenerator
from .styles import (
    CONTRACT_END_DATE,
    CONTRACT_PALETTE as C,
    DIMS,
    FONTS,
    TAX_RATE,
    TERMINATION_NOTICE_DAYS,
    hex_to_rgb,
)


class ContractPdfGenerator(BasePdfGenerator):

    def __init__(self, fonts_dir: Path | str):
        super().__init__(fonts_dir)
        self.company = CompanyInfo()

    def generate(self, emp: EmployeeData) -> bytes:
        pdf = self._create_pdf(emp.id)
        agreement_date = self.format_date(emp.agreement_date or date.today())
        effective_date = self.format_date(emp.effective_date or emp.agreement_date or date.today())

        self._title_page(pdf, emp, agreement_date, effective_date)
        self._content_pages(pdf, emp, agreement_date, effective_date)

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
        return f"Consulting Agreement {name}.pdf"

    # ── Title Page ──

    def _title_page(self, pdf: FPDF, emp: EmployeeData, agreement_date: str, effective_date: str) -> None:
        pdf.add_page()
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]

        # Brand
        pdf.set_y(30)
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "B", 32)
        self._set_color(pdf, C["NAVY"])
        ws_w = pdf.get_string_width("WOODENSHARK")
        pdf.cell(ws_w, 12, "WOODENSHARK")
        self._set_color(pdf, C["CYAN_DARK"])
        pdf.cell(0, 12, " LLC", new_x="LMARGIN", new_y="NEXT")

        # Cyan line
        y = pdf.get_y() + 2
        self._set_color(pdf, C["CYAN"], "draw")
        pdf.set_line_width(0.4)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 12)

        # Document title
        pdf.set_font(FONTS["HEADING"], "B", 28)
        self._set_color(pdf, C["NAVY"])
        pdf.cell(0, 10, "CONSULTING AGREEMENT", new_x="LMARGIN", new_y="NEXT")

        # Navy line
        y = pdf.get_y() + 2
        self._set_color(pdf, C["NAVY"], "draw")
        pdf.set_line_width(0.6)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)

        # Subtitle
        pdf.set_font(FONTS["HEADING"], "", 14)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(0, 8, "Professional Services & Technical Consulting", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() + 10)

        # Info table
        self._info_row(pdf, "AGREEMENT DATE", agreement_date)
        self._info_row(pdf, "EFFECTIVE DATE", effective_date)
        y = pdf.get_y() + 2
        self._set_color(pdf, C["LIGHT_GRAY"], "draw")
        pdf.set_line_width(0.15)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)
        self._info_row(pdf, "PARTY A (CLIENT)", self.company.name)
        self._info_row(pdf, "PARTY B (CONSULTANT)", emp.full_name_lat or "")

        # Classification badge
        pdf.set_y(260)
        pdf.set_font(FONTS["HEADING"], "", 9)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(32, 6, "CLASSIFICATION: ")
        self._set_color(pdf, C["NAVY"], "fill")
        pdf.set_text_color(255, 255, 255)
        pdf.cell(40, 6, "CONFIDENTIAL", fill=True, align="C")

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

    def _content_pages(self, pdf: FPDF, emp: EmployeeData, agreement_date: str, effective_date: str) -> None:
        pdf.add_page()
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        pdf.set_y(DIMS["CONTENT_TOP"] + 2)

        # Preamble
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, f"THIS CONSULTING AGREEMENT (the \u201cAgreement\u201d) dated {agreement_date}", align="J")
        pdf.ln(4)

        # BETWEEN
        pdf.set_font(FONTS["HEADING"], "B", 12)
        self._set_color(pdf, C["DARK"])
        pdf.cell(0, 6, "BETWEEN:", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Party boxes
        self._party_boxes(pdf, emp)

        # BACKGROUND (Section 1)
        self._section_heading(pdf, "1. BACKGROUND")
        for text in S.BACKGROUND:
            self._body_para(pdf, text)

        # Client details
        self._body_para(
            pdf,
            f"{self.company.name}, a company incorporated and registered in the United States of America "
            f"whose registered office is at {self.company.address_flat} (hereinafter the \u201cClient\u201d)"
        )

        # Employee details
        dob = self.format_date(emp.date_of_birth)
        pi = self.format_date(emp.passport_issued)
        pe = self.format_date(emp.passport_expires)
        self._body_para(
            pdf,
            f"{emp.full_name_lat or ''}, with the date of birth {dob}, the holder of Ukrainian Foreign Passport "
            f"\u2116 {emp.passport_number} issued on {pi} and valid till {pe}, "
            f"with the primary address of residence {emp.address or ''}"
        )

        # IN CONSIDERATION
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(cw, 5, S.IN_CONSIDERATION, align="J")
        pdf.ln(3)

        # Sections 2-23
        rate = emp.rate_usd
        total_with_tax = round(rate * (1 + TAX_RATE))
        rate_words = self.number_to_words(rate)
        total_words = self.number_to_words(total_with_tax)
        rate_fmt = f"{int(rate):,}"
        total_fmt = f"{total_with_tax:,}"

        for idx, (title, paragraphs) in enumerate(S.SECTIONS):
            section_num = idx + 2
            self._section_heading(pdf, f"{section_num}. {title}")

            for text in paragraphs:
                if text is None:
                    # Special content
                    if title == "SERVICES PROVIDED":
                        self._callout_box(pdf, emp.service_description or "UAV Systems Development Services")
                    elif title == "NOTICE":
                        self._notice_boxes(pdf, emp)
                    elif title == "COMPENSATION":
                        comp_text = (
                            f"The Consultant will charge the Client for the Services at the rate of "
                            f"{rate_fmt} ({rate_words}) USD plus {int(TAX_RATE * 100)}% tax, totaling "
                            f"{total_fmt} ({total_words}) USD per month (the \u201cCompensation\u201d) "
                            f"for full time employment."
                        )
                        self._body_para(pdf, comp_text)
                else:
                    rendered = text.replace("{end_date}", CONTRACT_END_DATE)
                    rendered = rendered.replace("{notice_days}", str(TERMINATION_NOTICE_DAYS))
                    self._body_para(pdf, rendered)

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
        self._set_color(pdf, C["DARK"])
        pdf.cell(cw, 7, title, new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        self._set_color(pdf, C["CYAN"], "draw")
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

    def _callout_box(self, pdf: FPDF, text: str) -> None:
        self._check_page_break(pdf, 16)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        y = pdf.get_y()
        self._set_color(pdf, C["CYAN_TINT"], "fill")
        self._set_color(pdf, C["LIGHT_GRAY"], "draw")
        pdf.set_line_width(0.3)
        pdf.rect(ml, y, cw, 12, style="DF")
        self._set_color(pdf, C["CYAN"], "fill")
        pdf.rect(ml, y, 1.2, 12, style="F")
        pdf.set_xy(ml + 4, y + 2)
        pdf.set_font(FONTS["HEADING"], "B", 13)
        self._set_color(pdf, C["DARK"])
        pdf.cell(cw - 8, 8, text, align="C")
        pdf.set_y(y + 14)

    def _notice_boxes(self, pdf: FPDF, emp: EmployeeData) -> None:
        self._check_page_break(pdf, 16)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]

        self._set_color(pdf, C["LIGHT_GRAY"], "draw")
        pdf.set_line_width(0.15)

        # Client notice
        y = pdf.get_y()
        pdf.line(ml, y + 8, ml + cw, y + 8)
        pdf.set_xy(ml + 4, y + 1)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(60, 5, self.company.name)
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(0, 5, "mitgor@woodenshark.com", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(y + 10)

        # Consultant notice
        y = pdf.get_y()
        pdf.line(ml, y + 8, ml + cw, y + 8)
        pdf.set_xy(ml + 4, y + 1)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(60, 5, emp.full_name_lat or "")
        pdf.set_font(FONTS["BODY"], "", 11)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(0, 5, emp.work_email or emp.phone or "", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(y + 12)

    def _party_boxes(self, pdf: FPDF, emp: EmployeeData) -> None:
        self._check_page_break(pdf, 40)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]
        box_w = (cw - 6) / 2
        y_start = pdf.get_y()

        # Client box
        self._set_color(pdf, C["FAFBFC"], "fill")
        self._set_color(pdf, C["CYAN"], "draw")
        pdf.set_line_width(0.5)
        pdf.rect(ml, y_start, box_w, 32, style="DF")
        self._set_color(pdf, C["CYAN"], "fill")
        pdf.rect(ml, y_start, 0.8, 32, style="F")

        pdf.set_xy(ml + 4, y_start + 3)
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["CYAN_DARK"])
        pdf.cell(0, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
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
        pdf.set_x(ml + 4)
        pdf.set_font(FONTS["BODY"], "I", 10)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(0, 4, '(the \u201cClient\u201d)', new_x="LEFT", new_y="NEXT")

        # Consultant box
        x2 = ml + box_w + 6
        self._set_color(pdf, C["FAFBFC"], "fill")
        self._set_color(pdf, C["CYAN"], "draw")
        pdf.rect(x2, y_start, box_w, 32, style="DF")
        self._set_color(pdf, C["CYAN"], "fill")
        pdf.rect(x2, y_start, 0.8, 32, style="F")

        pdf.set_xy(x2 + 4, y_start + 3)
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["CYAN_DARK"])
        pdf.cell(0, 4, "CONSULTANT", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2 + 4)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(0, 5, emp.full_name_lat or "", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2 + 4)
        pdf.set_font(FONTS["BODY"], "", 10)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(0, 4, emp.address or "", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2 + 4)
        pdf.set_font(FONTS["BODY"], "I", 10)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(0, 4, '(the \u201cConsultant\u201d)', new_x="LEFT", new_y="NEXT")

        pdf.set_y(y_start + 36)

    def _signature_block(self, pdf: FPDF, emp: EmployeeData, effective_date: str) -> None:
        self._check_page_break(pdf, 80)
        ml = DIMS["MARGIN_LEFT"]
        cw = DIMS["CONTENT_W"]

        # Navy line
        pdf.ln(6)
        y = pdf.get_y()
        self._set_color(pdf, C["NAVY"], "draw")
        pdf.set_line_width(0.8)
        pdf.line(ml, y, ml + cw, y)
        pdf.set_y(y + 4)

        # Witness
        pdf.set_font(FONTS["BODY"], "I", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.set_x(ml)
        pdf.multi_cell(
            cw, 5,
            f"IN WITNESS WHEREOF the Parties have duly affixed their signatures under hand and seal on {effective_date}.",
            align="J",
        )
        pdf.ln(4)

        box_w = (cw - 6) / 2
        y_start = pdf.get_y()

        # Client signature
        self._set_color(pdf, C["CYAN"], "draw")
        pdf.set_line_width(0.4)
        pdf.line(ml, y_start, ml + box_w, y_start)
        pdf.set_xy(ml, y_start + 2)

        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["CYAN_DARK"])
        pdf.cell(box_w, 4, "CLIENT", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(box_w, 5, self.company.name, new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["BODY"], "", 9)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        for line in self.company.address.split("\n"):
            pdf.cell(box_w, 3.5, line, new_x="LEFT", new_y="NEXT")
            pdf.set_x(ml)

        # Bank details
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 5, "Bank account:", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["BODY"], "", 9)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 3.5, f"SWIFT: {self.company.swift}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.cell(box_w, 3.5, f"Account: {self.company.account}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.cell(box_w, 3.5, self.company.bank, new_x="LEFT", new_y="NEXT")
        pdf.ln(3)
        pdf.set_x(ml)
        self._set_color(pdf, C["NAVY"])
        pdf.cell(box_w, 5, "____________________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(ml)
        pdf.set_font(FONTS["HEADING"], "", 8)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 4, "Signature", new_x="LEFT", new_y="NEXT")

        # Consultant signature
        x2 = ml + box_w + 6
        pdf.set_xy(x2, y_start)
        self._set_color(pdf, C["CYAN"], "draw")
        pdf.line(x2, y_start, x2 + box_w, y_start)
        pdf.set_xy(x2, y_start + 2)

        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["CYAN_DARK"])
        pdf.cell(box_w, 4, "CONSULTANT", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "B", 11)
        self._set_color(pdf, C["TEXT_PRIMARY"])
        pdf.cell(box_w, 5, emp.full_name_lat or "", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "", 9)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 3.5, emp.address or "", new_x="LEFT", new_y="NEXT")

        # Bank details
        pdf.set_x(x2)
        pdf.set_font(FONTS["HEADING"], "B", 9)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 5, "Bank account:", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["BODY"], "", 9)
        self._set_color(pdf, C["TEXT_SECONDARY"])
        pdf.cell(box_w, 3.5, f"IBAN: {emp.iban}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.cell(box_w, 3.5, f"SWIFT/BIC: {emp.swift}", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.cell(box_w, 3.5, f"Receiver: {emp.receiver_name}", new_x="LEFT", new_y="NEXT")
        pdf.ln(3)
        pdf.set_x(x2)
        self._set_color(pdf, C["NAVY"])
        pdf.cell(box_w, 5, "____________________________", new_x="LEFT", new_y="NEXT")
        pdf.set_x(x2)
        pdf.set_font(FONTS["HEADING"], "", 8)
        self._set_color(pdf, C["TEXT_MUTED"])
        pdf.cell(box_w, 4, emp.full_name_lat or "", new_x="LEFT", new_y="NEXT")

    # ── Header / Footer ──

    def _draw_header(self, pdf: FPDF, page: int, total: int) -> None:
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 0, 210, 15, style="F")

        r, g, b = hex_to_rgb(C["NAVY"])
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, 210, 7, style="F")
        pdf.set_font(FONTS["HEADING"], "", 6)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 2)
        pdf.cell(210, 4, "CONFIDENTIAL  \u2014  WOODENSHARK LLC PROPRIETARY", align="C")

        pdf.set_font(FONTS["HEADING"], "B", 7)
        r, g, b = hex_to_rgb(C["DARK"])
        pdf.set_text_color(r, g, b)
        pdf.set_xy(18, 8)
        pdf.cell(0, 4, "WOODENSHARK LLC")
        pdf.set_font(FONTS["HEADING"], "", 7)
        pdf.set_text_color(107, 107, 107)
        pdf.set_xy(0, 8)
        pdf.cell(192, 4, "Consulting Agreement", align="R")

        r, g, b = hex_to_rgb(C["CYAN"])
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.4)
        pdf.line(18, 13, 192, 13)

    def _draw_footer(self, pdf: FPDF, page: int, total: int) -> None:
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(0, 277, 210, 20, style="F")

        pdf.set_draw_color(208, 208, 208)
        pdf.set_line_width(0.15)
        pdf.line(18, 283, 192, 283)

        pdf.set_font(FONTS["HEADING"], "", 7)
        pdf.set_text_color(107, 107, 107)
        pdf.set_xy(0, 284)
        pdf.cell(210, 4, f"Consulting Services Agreement  |  CONFIDENTIAL  |  Page {page} of {total}", align="C")

        r, g, b = hex_to_rgb(C["NAVY"])
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 289, 210, 8, style="F")
        pdf.set_font(FONTS["HEADING"], "", 6)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 291)
        pdf.cell(210, 4, "CONFIDENTIAL  \u2014  WOODENSHARK LLC PROPRIETARY", align="C")
