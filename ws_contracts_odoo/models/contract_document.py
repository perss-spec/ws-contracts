import base64
import logging
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


class ContractDocument(models.Model):
    _name = "ws.contract.document"
    _description = "Contract Document"
    _order = "create_date desc"

    employee_id = fields.Many2one(
        "hr.employee", string="Employee",
        required=True, ondelete="cascade",
    )
    template_id = fields.Many2one(
        "ws.contract.template", string="Template",
        required=True, ondelete="restrict",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Generated"),
            ("sent_for_sign", "Sent for Signature"),
            ("signed", "Signed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    pdf_attachment_id = fields.Many2one(
        "ir.attachment", string="PDF File",
        ondelete="set null",
    )
    sign_request_id = fields.Many2one(
        "sign.request", string="Sign Request",
        ondelete="set null",
    )
    generated_date = fields.Datetime("Generated Date", readonly=True)
    signed_date = fields.Datetime("Signed Date", readonly=True)

    company_id = fields.Many2one(
        related="template_id.company_id", store=True, readonly=True,
    )
    doc_type = fields.Selection(
        related="template_id.doc_type", store=True, readonly=True,
    )

    def action_generate(self):
        """Generate PDF from template + employee data."""
        self.ensure_one()
        emp = self.employee_id
        data = emp._get_contract_data()

        from ..lib.pdf_generators import (
            generate_nda, generate_contract, EmployeeData,
        )

        emp_data = EmployeeData(**data)
        tmpl_data = self.template_id.to_template_data()

        if tmpl_data.doc_type == "nda":
            missing = emp_data.validate_for_nda()
            if missing:
                raise UserError(f"NDA: missing fields — {', '.join(missing)}")
            pdf_bytes, filename = generate_nda(emp_data, FONTS_DIR, template=tmpl_data)
        else:
            missing = emp_data.validate_for_contract()
            if missing:
                raise UserError(f"Contract: missing fields — {', '.join(missing)}")
            pdf_bytes, filename = generate_contract(emp_data, FONTS_DIR, template=tmpl_data)

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(pdf_bytes),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
        })

        self.write({
            "state": "generated",
            "pdf_attachment_id": attachment.id,
            "generated_date": fields.Datetime.now(),
        })

        return True

    def action_send_for_signature(self):
        """Send document for signature via Odoo Sign.

        Creates a sign.template from the PDF attachment, adds signature fields
        for both employee and company signatory, and sends the sign request.
        """
        self.ensure_one()
        if self.state != "generated":
            raise UserError("Document must be generated before sending for signature.")
        if not self.pdf_attachment_id:
            raise UserError("No PDF attachment found. Please generate the document first.")

        # Check if sign module is installed
        if not hasattr(self.env, "registry") or "sign.template" not in self.env:
            raise UserError(
                "Odoo Sign module is not installed. "
                "Please install 'sign' to use digital signatures."
            )

        try:
            sign_template = self._create_sign_template()
            sign_request = self._create_sign_request(sign_template)

            self.write({
                "state": "sent_for_sign",
                "sign_request_id": sign_request.id,
            })

            _logger.info(
                "Sign request %s created for document %s (employee: %s)",
                sign_request.id, self.id, self.employee_id.name,
            )

            return {
                "type": "ir.actions.act_window",
                "name": "Sign Request",
                "res_model": "sign.request",
                "res_id": sign_request.id,
                "view_mode": "form",
                "target": "current",
            }

        except Exception as e:
            _logger.exception("Failed to create sign request for document %s", self.id)
            raise UserError(f"Failed to send for signature: {e}") from e

    def _create_sign_template(self):
        """Create sign.template from the PDF attachment."""
        self.ensure_one()

        # Copy attachment for sign template
        sign_attachment = self.pdf_attachment_id.copy({
            "res_model": "sign.template",
            "res_id": 0,
        })

        sign_template = self.env["sign.template"].create({
            "attachment_id": sign_attachment.id,
        })

        # Add signature items (sign fields on the PDF)
        # Company signatory — bottom-left of last page
        self.env["sign.item"].create({
            "template_id": sign_template.id,
            "type_id": self.env.ref("sign.sign_item_type_signature").id,
            "responsible_id": self.env.ref("sign.sign_item_role_company_1").id,
            "page": 0,  # last page
            "posX": 0.05,
            "posY": 0.85,
            "width": 0.20,
            "height": 0.05,
            "required": True,
        })

        # Employee signature — bottom-right of last page
        self.env["sign.item"].create({
            "template_id": sign_template.id,
            "type_id": self.env.ref("sign.sign_item_type_signature").id,
            "responsible_id": self.env.ref("sign.sign_item_role_customer").id,
            "page": 0,
            "posX": 0.55,
            "posY": 0.85,
            "width": 0.20,
            "height": 0.05,
            "required": True,
        })

        return sign_template

    def _create_sign_request(self, sign_template):
        """Create sign.request and send to signers."""
        self.ensure_one()

        template = self.template_id
        emp = self.employee_id

        # Determine signers
        signers = []

        # Company signatory
        signatory_partner = False
        if template.signatory_email:
            signatory_partner = self.env["res.partner"].search(
                [("email", "=", template.signatory_email)], limit=1,
            )
        if not signatory_partner:
            signatory_partner = self.env.company.partner_id

        signers.append((0, 0, {
            "role_id": self.env.ref("sign.sign_item_role_company_1").id,
            "partner_id": signatory_partner.id,
        }))

        # Employee signer
        emp_partner = emp.user_id.partner_id if emp.user_id else False
        if not emp_partner and emp.work_email:
            emp_partner = self.env["res.partner"].search(
                [("email", "=", emp.work_email)], limit=1,
            )
        if not emp_partner:
            emp_partner = self.env["res.partner"].create({
                "name": emp.name,
                "email": emp.work_email,
                "type": "contact",
            })

        signers.append((0, 0, {
            "role_id": self.env.ref("sign.sign_item_role_customer").id,
            "partner_id": emp_partner.id,
        }))

        sign_request = self.env["sign.request"].create({
            "template_id": sign_template.id,
            "request_item_ids": signers,
            "subject": f"{template.doc_title or 'Document'} — {emp.name}",
            "message": f"Please review and sign the {template.doc_title or 'document'}.",
        })

        # Send the request
        sign_request.action_sent()

        return sign_request

    def action_mark_signed(self):
        """Manually mark document as signed (fallback if webhook misses)."""
        self.ensure_one()
        if self.state != "sent_for_sign":
            raise UserError("Document must be in 'Sent for Signature' state.")
        self.write({
            "state": "signed",
            "signed_date": fields.Datetime.now(),
        })

    def action_archive(self):
        self.ensure_one()
        self.write({"state": "archived"})

    @api.model
    def _cron_check_sign_status(self):
        """Cron job: check sign.request status and update document state."""
        docs = self.search([
            ("state", "=", "sent_for_sign"),
            ("sign_request_id", "!=", False),
        ])
        for doc in docs:
            try:
                request = doc.sign_request_id
                if request.state == "signed":
                    doc.write({
                        "state": "signed",
                        "signed_date": fields.Datetime.now(),
                    })
                    _logger.info("Document %s marked as signed (sign request %s)", doc.id, request.id)
            except Exception:
                _logger.exception("Error checking sign status for document %s", doc.id)
