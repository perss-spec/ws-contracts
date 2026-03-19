"""Tests for NDA PDF generation."""

import pytest
from pypdf import PdfReader
from io import BytesIO

from ws_contracts.config import PdfSettings
from ws_contracts.models import EmployeeData
from ws_contracts.pdf.nda import NdaPdfGenerator


FONTS_DIR = PdfSettings(fonts_dir="fonts").fonts_dir


@pytest.fixture
def nda_gen(pdf_settings: PdfSettings) -> NdaPdfGenerator:
    return NdaPdfGenerator(pdf_settings.fonts_dir)


@pytest.fixture
def nda_pdf_bytes(nda_gen: NdaPdfGenerator, sample_employee: EmployeeData) -> bytes:
    return nda_gen.generate(sample_employee)


class TestNdaPdf:

    def test_generates_valid_pdf(self, nda_pdf_bytes: bytes):
        assert nda_pdf_bytes[:5] == b"%PDF-"
        assert len(nda_pdf_bytes) > 1000

    def test_has_correct_pages(self, nda_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(nda_pdf_bytes))
        assert len(reader.pages) >= 3

    def test_contains_employee_name(self, nda_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(nda_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "Oleksandr Petrenko" in all_text

    def test_contains_nda_title(self, nda_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(nda_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "NON-DISCLOSURE AGREEMENT" in all_text

    def test_filename(self, nda_gen: NdaPdfGenerator, sample_employee: EmployeeData):
        assert nda_gen.get_filename(sample_employee) == "NDA Oleksandr Petrenko.pdf"

    def test_filename_unknown(self, nda_gen: NdaPdfGenerator):
        emp = EmployeeData()
        assert nda_gen.get_filename(emp) == "NDA Unknown.pdf"

    def test_watermark_present(self, nda_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(nda_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "CONFIDENTIAL" in all_text

    def test_encryption_applied(self, nda_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(nda_pdf_bytes))
        assert reader.is_encrypted
