"""Domain models: EmployeeData, CompanyInfo."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


def _validate_iban(v: str) -> str:
    cleaned = v.replace(" ", "").upper()
    if len(cleaned) < 15 or len(cleaned) > 34:
        raise ValueError(f"IBAN length must be 15-34 chars, got {len(cleaned)}")
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", cleaned):
        raise ValueError("IBAN must start with 2 letters + 2 digits")
    return cleaned


def _validate_swift(v: str) -> str:
    cleaned = v.replace(" ", "").upper()
    if not re.match(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$", cleaned):
        raise ValueError("SWIFT/BIC must be 8 or 11 alphanumeric chars")
    return cleaned


class EmployeeData(BaseModel):
    id: int | str = 0
    full_name_lat: str = ""
    date_of_birth: Optional[date] = None
    passport_number: str = ""
    passport_issued: Optional[date] = None
    passport_expires: Optional[date] = None
    address: str = ""
    work_email: str = ""
    phone: str = ""
    iban: str = ""
    swift: str = "UNJSUAUKXXX"
    receiver_name: str = ""
    rate_usd: float = 0.0
    service_description: str = "UAV Systems Development Services"
    agreement_date: Optional[date] = None
    effective_date: Optional[date] = None

    @field_validator("iban", mode="before")
    @classmethod
    def clean_iban(cls, v: str) -> str:
        if not v:
            return v
        return _validate_iban(v)

    @field_validator("swift", mode="before")
    @classmethod
    def clean_swift(cls, v: str) -> str:
        if not v:
            return v
        return _validate_swift(v)

    def validate_for_nda(self) -> list[str]:
        """Return list of missing field labels required for NDA."""
        checks = {
            "Full Name (Latin)": self.full_name_lat,
            "Date of Birth": self.date_of_birth,
            "Passport Number": self.passport_number,
            "Passport Issued": self.passport_issued,
            "Passport Expires": self.passport_expires,
            "Address": self.address,
        }
        return [label for label, val in checks.items() if not val]

    def validate_for_contract(self) -> list[str]:
        """Return list of missing field labels required for Contract."""
        missing = self.validate_for_nda()
        extra = {
            "IBAN": self.iban,
            "SWIFT": self.swift,
            "Receiver Name": self.receiver_name,
            "Rate (USD)": self.rate_usd,
        }
        missing.extend(label for label, val in extra.items() if not val)
        return missing


class CompanyInfo(BaseModel):
    name: str = "Woodenshark LLC"
    address: str = "3411 Silverside Road, Suite 104\nWilmington, DE 19810, USA"
    address_flat: str = "3411 Silverside Road, Suite 104, Rodney Building, Wilmington, DE, 19810"
    swift: str = "CMFGUS33"
    account: str = "822000034828"
    bank: str = "Wise Inc"
