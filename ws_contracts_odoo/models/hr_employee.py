import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # ── Contract Details fields ──
    ws_full_name_lat = fields.Char("Full Name (Latin)")
    ws_passport_number = fields.Char("Passport Number")
    ws_passport_issued = fields.Date("Passport Issued")
    ws_passport_expires = fields.Date("Passport Expires")
    ws_address_full = fields.Text("Full Address")
    ws_iban = fields.Char("IBAN")
    ws_swift = fields.Char("SWIFT/BIC", default="UNJSUAUKXXX")
    ws_receiver_name = fields.Char("Bank Receiver Name")
    ws_rate_usd = fields.Float("Rate (USD/month)")
    ws_service_description = fields.Char(
        "Service Description",
        default="UAV Systems Development Services",
    )
    ws_agreement_date = fields.Date("Agreement Date")
    ws_effective_date = fields.Date("Effective Date")

    # ── Document relations ──
    ws_document_ids = fields.One2many(
        "ws.contract.document", "employee_id",
        string="Contract Documents",
    )
    ws_document_count = fields.Integer(
        compute="_compute_ws_document_count", string="Documents",
    )
    ws_pending_sign_count = fields.Integer(
        compute="_compute_ws_pending_sign_count", string="Pending Sign",
    )

    @api.depends("ws_document_ids")
    def _compute_ws_document_count(self):
        for rec in self:
            rec.ws_document_count = len(rec.ws_document_ids)

    @api.depends("ws_document_ids.state")
    def _compute_ws_pending_sign_count(self):
        for rec in self:
            rec.ws_pending_sign_count = len(
                rec.ws_document_ids.filtered(
                    lambda d: d.state in ("generated", "sent_for_sign")
                )
            )

    def action_view_contract_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contract Documents",
            "res_model": "ws.contract.document",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }

    def action_view_pending_sign_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Pending Signature",
            "res_model": "ws.contract.document",
            "view_mode": "list,form",
            "domain": [
                ("employee_id", "=", self.id),
                ("state", "in", ("generated", "sent_for_sign")),
            ],
            "context": {"default_employee_id": self.id},
        }

    def action_generate_documents(self):
        """Open the document generation wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generate Documents",
            "res_model": "ws.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_employee_id": self.id},
        }

    def _get_contract_data(self):
        """Return dict with employee data for PDF generation."""
        self.ensure_one()
        return {
            "id": self.id,
            "full_name_lat": self.ws_full_name_lat or self.name or "",
            "date_of_birth": self.birthday,
            "passport_number": self.ws_passport_number or "",
            "passport_issued": self.ws_passport_issued,
            "passport_expires": self.ws_passport_expires,
            "address": self.ws_address_full or "",
            "work_email": self.work_email or "",
            "phone": self.work_phone or "",
            "iban": self.ws_iban or "",
            "swift": self.ws_swift or "UNJSUAUKXXX",
            "receiver_name": self.ws_receiver_name or "",
            "rate_usd": self.ws_rate_usd or 0.0,
            "service_description": self.ws_service_description or "UAV Systems Development Services",
            "agreement_date": self.ws_agreement_date,
            "effective_date": self.ws_effective_date,
        }
