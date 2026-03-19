import base64
import logging
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


def _sign_installed(env):
    """Check if Odoo Sign module is installed at runtime."""
    return "sign.template" in env.registry


class ContractDocument(models.Model):
    _name = "ws.contract.document"
    _description = "Contract Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
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
        copy=False,
        tracking=True,
    )
    pdf_attachment_id = fields.Many2one(
        "ir.attachment", string="PDF File",
        ondelete="set null", copy=False,
    )
    # Store sign request ID as Integer to avoid hard dependency on sign module
    sign_request_id = fields.Integer(
        "Sign Request ID", copy=False, readonly=True,
    )
    generated_date = fields.Datetime("Generated Date", readonly=True, copy=False)
    signed_date = fields.Datetime("Signed Date", readonly=True, copy=False)

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
        """Send document for signature via Odoo Sign."""
        self.ensure_one()
        if self.state != "generated":
            raise UserError("Document must be generated before sending for signature.")
        if not self.pdf_attachment_id:
            raise UserError("No PDF attachment found. Please generate the document first.")
        if not _sign_installed(self.env):
            raise UserError(
                "Odoo Sign module is not installed. "
                "Please install 'sign' to use digital signatures."
            )

        emp = self.employee_id
        if not emp.work_email:
            raise UserError(
                f"Employee '{emp.name}' has no work email. "
                "An email is required for digital signature."
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
                sign_request.id, self.id, emp.name,
            )

            return {
                "type": "ir.actions.act_window",
                "name": "Sign Request",
                "res_model": "sign.request",
                "res_id": sign_request.id,
                "view_mode": "form",
                "target": "current",
            }

        except UserError:
            raise
        except Exception as e:
            _logger.exception("Failed to create sign request for document %s", self.id)
            raise UserError(f"Failed to send for signature: {e}") from e

    def _create_sign_template(self):
        """Create sign.template from the PDF attachment."""
        self.ensure_one()
        SignTemplate = self.env["sign.template"]
        SignItem = self.env["sign.item"]

        sign_attachment = self.pdf_attachment_id.copy({
            "res_model": "sign.template",
            "res_id": 0,
        })

        sign_template = SignTemplate.create({
            "attachment_id": sign_attachment.id,
        })

        sig_type = self.env.ref("sign.sign_item_type_signature", raise_if_not_found=False)
        role_company = self.env.ref("sign.sign_item_role_company_1", raise_if_not_found=False)
        role_customer = self.env.ref("sign.sign_item_role_customer", raise_if_not_found=False)

        if not sig_type or not role_company or not role_customer:
            raise UserError(
                "Odoo Sign data records not found. "
                "Please ensure the Sign module is properly installed."
            )

        for role, pos_x in [(role_company, 0.05), (role_customer, 0.55)]:
            SignItem.create({
                "template_id": sign_template.id,
                "type_id": sig_type.id,
                "responsible_id": role.id,
                "page": 0,
                "posX": pos_x,
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

        role_company = self.env.ref("sign.sign_item_role_company_1")
        role_customer = self.env.ref("sign.sign_item_role_customer")

        # Company signatory
        signatory_partner = False
        if template.signatory_email:
            signatory_partner = self.env["res.partner"].search(
                [("email", "=", template.signatory_email)], limit=1,
            )
        if not signatory_partner:
            signatory_partner = self.env.company.partner_id

        # Employee signer
        emp_partner = emp.user_id.partner_id if emp.user_id else False
        if not emp_partner:
            emp_partner = self.env["res.partner"].search(
                [("email", "=", emp.work_email)], limit=1,
            )
        if not emp_partner:
            emp_partner = self.env["res.partner"].create({
                "name": emp.name,
                "email": emp.work_email,
                "type": "contact",
            })

        sign_request = self.env["sign.request"].create({
            "template_id": sign_template.id,
            "request_item_ids": [
                (0, 0, {"role_id": role_company.id, "partner_id": signatory_partner.id}),
                (0, 0, {"role_id": role_customer.id, "partner_id": emp_partner.id}),
            ],
            "subject": f"{template.doc_title or 'Document'} — {emp.name}",
            "message": f"Please review and sign the {template.doc_title or 'document'}.",
        })

        sign_request.action_sent()
        return sign_request

    def action_mark_signed(self):
        """Manually mark document as signed."""
        self.ensure_one()
        if self.state != "sent_for_sign":
            raise UserError("Document must be in 'Sent for Signature' state.")
        self.write({
            "state": "signed",
            "signed_date": fields.Datetime.now(),
        })

    def action_move_to_archive(self):
        """Move document to archived state."""
        self.ensure_one()
        self.write({"state": "archived"})

    @api.model
    def _cron_check_sign_status(self):
        """Cron job: check sign.request status and update document state."""
        if not _sign_installed(self.env):
            return

        SignRequest = self.env["sign.request"]
        docs = self.search([
            ("state", "=", "sent_for_sign"),
            ("sign_request_id", "!=", 0),
        ])
        for doc in docs:
            try:
                request = SignRequest.browse(doc.sign_request_id)
                if request.exists() and request.state == "signed":
                    doc.write({
                        "state": "signed",
                        "signed_date": fields.Datetime.now(),
                    })
                    _logger.info(
                        "Document %s marked as signed (sign request %s)",
                        doc.id, doc.sign_request_id,
                    )
            except Exception:
                _logger.exception(
                    "Error checking sign status for document %s", doc.id,
                )
