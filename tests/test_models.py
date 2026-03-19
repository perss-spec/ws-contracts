"""Tests for models.py — EmployeeData validation."""

import pytest
from ws_contracts.models import EmployeeData


class TestEmployeeData:

    def test_valid_data(self, sample_employee: EmployeeData):
        assert sample_employee.full_name_lat == "Oleksandr Petrenko"
        assert sample_employee.rate_usd == 3000
        assert sample_employee.iban == "UA213223130000026007233566001"

    def test_missing_nda_fields(self):
        emp = EmployeeData(full_name_lat="Test")
        missing = emp.validate_for_nda()
        assert "Date of Birth" in missing
        assert "Passport Number" in missing
        assert "Address" in missing
        assert "Full Name (Latin)" not in missing

    def test_missing_contract_fields(self):
        emp = EmployeeData(full_name_lat="Test")
        missing = emp.validate_for_contract()
        assert "IBAN" in missing
        assert "Rate (USD)" in missing
        assert "Receiver Name" in missing

    def test_nda_valid_complete(self, sample_employee: EmployeeData):
        assert sample_employee.validate_for_nda() == []

    def test_contract_valid_complete(self, sample_employee: EmployeeData):
        assert sample_employee.validate_for_contract() == []

    def test_iban_validation_valid(self):
        emp = EmployeeData(iban="UA213223130000026007233566001")
        assert emp.iban == "UA213223130000026007233566001"

    def test_iban_validation_with_spaces(self):
        emp = EmployeeData(iban="UA21 3223 1300 0002 6007 2335 66001")
        assert emp.iban == "UA213223130000026007233566001"

    def test_iban_validation_invalid_short(self):
        with pytest.raises(ValueError, match="IBAN length"):
            EmployeeData(iban="UA123")

    def test_iban_validation_invalid_format(self):
        with pytest.raises(ValueError, match="IBAN must start"):
            EmployeeData(iban="1234567890123456")

    def test_swift_validation_valid_8(self):
        emp = EmployeeData(swift="CMFGUS33")
        assert emp.swift == "CMFGUS33"

    def test_swift_validation_valid_11(self):
        emp = EmployeeData(swift="UNJSUAUKXXX")
        assert emp.swift == "UNJSUAUKXXX"

    def test_swift_validation_invalid(self):
        with pytest.raises(ValueError, match="SWIFT"):
            EmployeeData(swift="INVALID")

    def test_empty_iban_allowed(self):
        emp = EmployeeData(iban="")
        assert emp.iban == ""

    def test_empty_swift_allowed(self):
        emp = EmployeeData(swift="")
        assert emp.swift == ""
