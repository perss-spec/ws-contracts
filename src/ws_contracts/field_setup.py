"""Create custom x_ fields in hr.employee via ir.model.fields."""

from __future__ import annotations

from .odoo_client import OdooClient

CUSTOM_FIELDS = [
    {"name": "x_full_name_lat",       "ttype": "char",  "field_description": "Full Name (Latin)"},
    {"name": "x_passport_number",     "ttype": "char",  "field_description": "Passport Number"},
    {"name": "x_passport_issued",     "ttype": "date",  "field_description": "Passport Issued Date"},
    {"name": "x_passport_expires",    "ttype": "date",  "field_description": "Passport Expiry Date"},
    {"name": "x_address_full",        "ttype": "text",  "field_description": "Full Address"},
    {"name": "x_iban",                "ttype": "char",  "field_description": "IBAN"},
    {"name": "x_swift",               "ttype": "char",  "field_description": "SWIFT/BIC"},
    {"name": "x_receiver_name",       "ttype": "char",  "field_description": "Bank Receiver Name"},
    {"name": "x_rate_usd",            "ttype": "float", "field_description": "Rate USD/month"},
    {"name": "x_service_description", "ttype": "char",  "field_description": "Service Description"},
    {"name": "x_agreement_date",      "ttype": "date",  "field_description": "Agreement Date"},
    {"name": "x_effective_date",      "ttype": "date",  "field_description": "Effective Date"},
]

HR_EMPLOYEE_MODEL = "hr.employee"


def get_model_id(client: OdooClient) -> int:
    records = client.search_read("ir.model", [["model", "=", HR_EMPLOYEE_MODEL]], fields=["id"], limit=1)
    if not records:
        raise ValueError(f"Model {HR_EMPLOYEE_MODEL} not found in Odoo")
    return records[0]["id"]


def get_existing_fields(client: OdooClient, model_id: int) -> set[str]:
    records = client.search_read(
        "ir.model.fields",
        [["model_id", "=", model_id], ["name", "like", "x_"]],
        fields=["name"],
    )
    return {r["name"] for r in records}


def sync_fields(client: OdooClient, dry_run: bool = False) -> list[str]:
    """Create missing x_ fields. Returns list of created field names."""
    model_id = get_model_id(client)
    existing = get_existing_fields(client, model_id)
    created = []

    for field_def in CUSTOM_FIELDS:
        if field_def["name"] in existing:
            continue
        if dry_run:
            created.append(field_def["name"])
            continue
        client.create("ir.model.fields", {
            "model_id": model_id,
            "name": field_def["name"],
            "ttype": field_def["ttype"],
            "field_description": field_def["field_description"],
        })
        created.append(field_def["name"])

    return created
