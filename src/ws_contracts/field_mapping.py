"""Map Odoo hr.employee record → EmployeeData."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .models import EmployeeData

# Standard Odoo fields + custom x_ fields
ODOO_FIELDS = [
    "id", "name", "birthday", "work_email", "work_phone",
    "x_full_name_lat", "x_passport_number", "x_passport_issued",
    "x_passport_expires", "x_address_full", "x_iban", "x_swift",
    "x_receiver_name", "x_rate_usd", "x_service_description",
    "x_agreement_date", "x_effective_date",
]


def _parse_date(val: Any) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).date()
        except ValueError:
            return date.fromisoformat(val)
    return None


def map_employee(record: dict[str, Any]) -> EmployeeData:
    """Convert Odoo record dict to EmployeeData."""
    return EmployeeData(
        id=record.get("id", 0),
        full_name_lat=record.get("x_full_name_lat") or record.get("name") or "",
        date_of_birth=_parse_date(record.get("birthday")),
        passport_number=record.get("x_passport_number") or "",
        passport_issued=_parse_date(record.get("x_passport_issued")),
        passport_expires=_parse_date(record.get("x_passport_expires")),
        address=record.get("x_address_full") or "",
        work_email=record.get("work_email") or "",
        phone=record.get("work_phone") or "",
        iban=record.get("x_iban") or "",
        swift=record.get("x_swift") or "UNJSUAUKXXX",
        receiver_name=record.get("x_receiver_name") or "",
        rate_usd=float(record.get("x_rate_usd") or 0),
        service_description=record.get("x_service_description") or "UAV Systems Development Services",
        agreement_date=_parse_date(record.get("x_agreement_date")),
        effective_date=_parse_date(record.get("x_effective_date")),
    )
