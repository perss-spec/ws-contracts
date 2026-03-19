"""Tests for field_mapping.py."""

from datetime import date

from ws_contracts.field_mapping import map_employee


class TestFieldMapping:

    def test_standard_field_birthday(self, sample_employee_data: dict):
        odoo_record = {
            "id": 1,
            "name": "Test",
            "birthday": "1990-05-15",
            "work_email": "",
            "work_phone": "",
            "x_full_name_lat": "",
            "x_passport_number": "",
            "x_passport_issued": False,
            "x_passport_expires": False,
            "x_address_full": "",
            "x_iban": "",
            "x_swift": "",
            "x_receiver_name": "",
            "x_rate_usd": 0,
            "x_service_description": "",
            "x_agreement_date": False,
            "x_effective_date": False,
        }
        emp = map_employee(odoo_record)
        assert emp.date_of_birth == date(1990, 5, 15)

    def test_custom_field_iban(self):
        odoo_record = {
            "id": 2,
            "name": "Test",
            "birthday": False,
            "work_email": "",
            "work_phone": "",
            "x_full_name_lat": "Test Person",
            "x_passport_number": "AB123",
            "x_passport_issued": "2020-01-01",
            "x_passport_expires": "2030-01-01",
            "x_address_full": "Some address",
            "x_iban": "UA213223130000026007233566001",
            "x_swift": "UNJSUAUKXXX",
            "x_receiver_name": "Test Person",
            "x_rate_usd": 2500.0,
            "x_service_description": "Dev Services",
            "x_agreement_date": "2025-01-01",
            "x_effective_date": "2025-02-01",
        }
        emp = map_employee(odoo_record)
        assert emp.iban == "UA213223130000026007233566001"
        assert emp.full_name_lat == "Test Person"
        assert emp.rate_usd == 2500.0

    def test_fallback_name(self):
        odoo_record = {
            "id": 3,
            "name": "Fallback Name",
            "birthday": False,
            "work_email": "",
            "work_phone": "",
            "x_full_name_lat": "",
        }
        emp = map_employee(odoo_record)
        assert emp.full_name_lat == "Fallback Name"

    def test_false_date_is_none(self):
        odoo_record = {
            "id": 4,
            "name": "Test",
            "birthday": False,
        }
        emp = map_employee(odoo_record)
        assert emp.date_of_birth is None
