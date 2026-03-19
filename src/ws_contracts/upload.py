"""Upload generated PDF to Odoo as ir.attachment."""

from __future__ import annotations

import base64

from .odoo_client import OdooClient


def upload_pdf(client: OdooClient, employee_id: int, filename: str, pdf_bytes: bytes) -> int:
    """Upload PDF bytes as attachment to hr.employee record. Returns attachment id."""
    return client.create("ir.attachment", {
        "name": filename,
        "type": "binary",
        "datas": base64.b64encode(pdf_bytes).decode("ascii"),
        "res_model": "hr.employee",
        "res_id": employee_id,
        "mimetype": "application/pdf",
    })
