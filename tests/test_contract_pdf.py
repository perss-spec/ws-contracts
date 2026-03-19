"""Tests for Contract PDF generation."""

import pytest
from pypdf import PdfReader
from io import BytesIO

from ws_contracts.config import PdfSettings
from ws_contracts.models import EmployeeData
from ws_contracts.pdf.contract import ContractPdfGenerator
from ws_contracts.pdf.styles import TAX_RATE


@pytest.fixture
def contract_gen(pdf_settings: PdfSettings) -> ContractPdfGenerator:
    return ContractPdfGenerator(pdf_settings.fonts_dir)


@pytest.fixture
def contract_pdf_bytes(contract_gen: ContractPdfGenerator, sample_employee: EmployeeData) -> bytes:
    return contract_gen.generate(sample_employee)


class TestContractPdf:

    def test_generates_valid_pdf(self, contract_pdf_bytes: bytes):
        assert contract_pdf_bytes[:5] == b"%PDF-"
        assert len(contract_pdf_bytes) > 1000

    def test_has_correct_pages(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        assert len(reader.pages) >= 3

    def test_contains_employee_name(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "Oleksandr Petrenko" in all_text

    def test_contains_consulting_title(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "CONSULTING AGREEMENT" in all_text

    def test_compensation_math(self, sample_employee: EmployeeData):
        rate = sample_employee.rate_usd
        total = round(rate * (1 + TAX_RATE))
        assert total == 3180  # 3000 * 1.06

    def test_bank_details_in_text(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "UA213223130000026007233566001" in all_text
        assert "UNJSUAUKXXX" in all_text

    def test_filename(self, contract_gen: ContractPdfGenerator, sample_employee: EmployeeData):
        assert contract_gen.get_filename(sample_employee) == "Consulting Agreement Oleksandr Petrenko.pdf"

    def test_watermark_present(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text() or ""
        assert "CONFIDENTIAL" in all_text

    def test_encryption_applied(self, contract_pdf_bytes: bytes):
        reader = PdfReader(BytesIO(contract_pdf_bytes))
        assert reader.is_encrypted
