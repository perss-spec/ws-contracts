"""Shared fixtures for ws-contracts tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ws_contracts.config import PdfSettings
from ws_contracts.models import EmployeeData
from ws_contracts.odoo_client import OdooClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FONTS_DIR = Path(__file__).parent.parent / "fonts"


@pytest.fixture
def sample_employee_data() -> dict:
    return json.loads((FIXTURES_DIR / "sample_employee.json").read_text())


@pytest.fixture
def sample_employee(sample_employee_data: dict) -> EmployeeData:
    return EmployeeData(**sample_employee_data)


@pytest.fixture
def pdf_settings() -> PdfSettings:
    return PdfSettings(fonts_dir=FONTS_DIR)


@pytest.fixture
def mock_odoo_client(sample_employee_data: dict) -> OdooClient:
    client = MagicMock(spec=OdooClient)
    client.uid = 2

    # Map sample_employee_data to Odoo record format
    odoo_record = {
        "id": sample_employee_data["id"],
        "name": sample_employee_data["full_name_lat"],
        "birthday": sample_employee_data["date_of_birth"],
        "work_email": sample_employee_data["work_email"],
        "work_phone": sample_employee_data["phone"],
        "x_full_name_lat": sample_employee_data["full_name_lat"],
        "x_passport_number": sample_employee_data["passport_number"],
        "x_passport_issued": sample_employee_data["passport_issued"],
        "x_passport_expires": sample_employee_data["passport_expires"],
        "x_address_full": sample_employee_data["address"],
        "x_iban": sample_employee_data["iban"],
        "x_swift": sample_employee_data["swift"],
        "x_receiver_name": sample_employee_data["receiver_name"],
        "x_rate_usd": sample_employee_data["rate_usd"],
        "x_service_description": sample_employee_data["service_description"],
        "x_agreement_date": sample_employee_data["agreement_date"],
        "x_effective_date": sample_employee_data["effective_date"],
    }

    client.get_employee.return_value = odoo_record
    client.get_all_employees.return_value = [odoo_record]
    client.search_read.return_value = [odoo_record]
    client.create.return_value = 100
    return client
