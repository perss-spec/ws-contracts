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
        tracking=True,
    )
    template_id = fields.Many2one(
        "ws.contract.template", string="Template",
        required=True, ondelete="restrict",
        tracking=True,
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
        tracking=True,
    )
    # Store sign request ID as Integer to avoid hard dependency on sign module
    sign_request_id = fields.Integer(
        "Sign Request ID", copy=False, readonly=True,
    )
    generated_date = fields.Datetime("Generated Date", readonly=True, copy=False)
    signed_date = fields.Datetime("Signed Date", readonly=True, copy=False)

    # ── Polish contract fields ──
    signing_date = fields.Date("Signing Date")
    contract_start_date = fields.Date("Contract Start Date")
    contract_end_date = fields.Date("Contract End Date")
    job_title_pl = fields.Char("Job Title (PL)")
    job_title_en = fields.Char("Job Title (EN)")
    place_of_work = fields.Char("Place of Work", default="Lublin")
    working_time_pl = fields.Char("Working Time (PL)", default="pełny etat (1/1)")
    working_time_en = fields.Char("Working Time (EN)", default="full time (1/1)")
    salary_gross = fields.Float("Salary Gross (PLN/month)", digits=(10, 2))
    hourly_rate_gross = fields.Float("Hourly Rate Gross (PLN)", digits=(10, 2))
    scope_of_work_pl = fields.Text("Scope of Work (PL)")
    scope_of_work_en = fields.Text("Scope of Work (EN)")
    id_document_pl = fields.Char("ID Document (PL)", help="e.g. dowodem osobistym ABC 123456")
    id_document_en = fields.Char("ID Document (EN)", help="e.g. ID card ABC 123456")
    justification_pl = fields.Text("Extension Justification (PL)", help="For Probationary 2+1 only")
    justification_en = fields.Text("Extension Justification (EN)", help="For Probationary 2+1 only")

    company_id = fields.Many2one(
        related="template_id.company_id", store=True, readonly=True,
    )
    doc_type = fields.Selection(
        related="template_id.doc_type", store=True, readonly=True,
    )

    # ── Display name ──
    @api.depends("employee_id.name", "template_id.doc_title", "create_date")
    def _compute_display_name(self):
        for rec in self:
            emp = rec.employee_id.name or "?"
            doc = rec.template_id.doc_title or rec.doc_type or "Document"
            dt = rec.create_date.strftime("%Y-%m-%d") if rec.create_date else "draft"
            rec.display_name = f"{doc} — {emp} ({dt})"

    # ── Partial unique index: no duplicate drafts ──
    def init(self):
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ws_contract_doc_unique_draft
            ON ws_contract_document (employee_id, template_id)
            WHERE state = 'draft'
        """)

    def action_generate(self):
        """Generate PDF or DOCX from template + employee data."""
        self.ensure_one()
        # DOCX generation path
        if self.template_id.generation_method == "docx":
            return self._generate_docx()
        # Existing PDF generation path below...
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

    def _generate_docx(self):
        """Generate filled DOCX from template."""
        self.ensure_one()
        if not self.template_id.docx_template:
            raise UserError("No DOCX template file uploaded on the template record.")

        from ..lib.docx_generator import fill_docx_template

        # Collect placeholder values
        placeholders = self._collect_pl_placeholders()

        # Fill template
        docx_bytes = fill_docx_template(
            base64.b64decode(self.template_id.docx_template),
            placeholders,
        )

        filename = f"{self.template_id.doc_title or 'Document'}_{self.employee_id.name}_{fields.Date.today()}.docx"
        filename = filename.replace(" ", "_")

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(docx_bytes),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        })

        self.write({
            "state": "generated",
            "pdf_attachment_id": attachment.id,
            "generated_date": fields.Datetime.now(),
        })
        return True

    def _collect_pl_placeholders(self):
        """Collect all placeholder values for Polish DOCX template filling."""
        self.ensure_one()
        emp = self.employee_id
        data = emp._get_pl_contract_data()

        # Date formatting helpers
        def fmt_pl(d):
            """Format date as Polish: '17 marca 2026 r.'"""
            if not d:
                return ""
            months_pl = {
                1: "stycznia", 2: "lutego", 3: "marca", 4: "kwietnia",
                5: "maja", 6: "czerwca", 7: "lipca", 8: "sierpnia",
                9: "września", 10: "października", 11: "listopada", 12: "grudnia",
            }
            return f"{d.day} {months_pl[d.month]} {d.year} r."

        def fmt_en(d):
            """Format date as English: '17 March 2026'"""
            if not d:
                return ""
            months_en = {
                1: "January", 2: "February", 3: "March", 4: "April",
                5: "May", 6: "June", 7: "July", 8: "August",
                9: "September", 10: "October", 11: "November", 12: "December",
            }
            return f"{d.day} {months_en[d.month]} {d.year}"

        def fmt_pln(amount):
            """Format amount with Polish decimal separator (comma)."""
            return f"{amount:,.2f}".replace(",", " ").replace(".", ",")

        def fmt_pln_en(amount):
            """Format amount with English decimal separator (period)."""
            return f"{amount:,.2f}".replace(",", " ")

        # Dates
        data["DATA_ZAWARCIA"] = fmt_pl(self.signing_date)
        data["DATA_ZAWARCIA_EN"] = fmt_en(self.signing_date)

        # Employment contract dates
        data["DATA_OD"] = fmt_pl(self.contract_start_date)
        data["DATA_OD_EN"] = fmt_en(self.contract_start_date)
        data["DATA_DO"] = fmt_pl(self.contract_end_date)
        data["DATA_DO_EN"] = fmt_en(self.contract_end_date)

        # Zlecenie dates (same data, different placeholder names)
        data["DATA_ROZPOCZECIA"] = fmt_pl(self.contract_start_date)
        data["DATA_ROZPOCZECIA_EN"] = fmt_en(self.contract_start_date)
        data["DATA_ZAKONCZENIA"] = fmt_pl(self.contract_end_date)
        data["DATA_ZAKONCZENIA_EN"] = fmt_en(self.contract_end_date)

        # Job details
        data["STANOWISKO_PL"] = self.job_title_pl or ""
        data["STANOWISKO_EN"] = self.job_title_en or ""
        data["MIEJSCE_PRACY"] = self.place_of_work or "Lublin"
        data["WYMIAR_ETATU"] = self.working_time_pl or "pełny etat (1/1)"
        data["WYMIAR_ETATU_EN"] = self.working_time_en or "full time (1/1)"

        # Salary
        data["KWOTA_BRUTTO"] = fmt_pln(self.salary_gross) if self.salary_gross else ""
        data["KWOTA_BRUTTO_EN"] = fmt_pln_en(self.salary_gross) if self.salary_gross else ""
        data["STAWKA_BRUTTO"] = fmt_pln(self.hourly_rate_gross) if self.hourly_rate_gross else ""
        data["STAWKA_BRUTTO_EN"] = fmt_pln_en(self.hourly_rate_gross) if self.hourly_rate_gross else ""

        # Zlecenie-specific
        data["ZAKRES_CZYNNOSCI_PL"] = self.scope_of_work_pl or ""
        data["ZAKRES_CZYNNOSCI_EN"] = self.scope_of_work_en or ""
        data["DOKUMENT_TOZSAMOSCI"] = self.id_document_pl or ""
        data["DOKUMENT_TOZSAMOSCI_EN"] = self.id_document_en or ""

        # 2+1 extension justification
        data["UZASADNIENIE_PL"] = self.justification_pl or ""
        data["UZASADNIENIE_EN"] = self.justification_en or ""

        return data

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
        role_company = self.env.ref("sign.sign_item_role_user", raise_if_not_found=False)
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

        role_company = self.env.ref("sign.sign_item_role_user")
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

    # ── Bulk actions (called from server actions) ──
    def action_bulk_generate(self):
        """Generate PDF for selected draft documents."""
        drafts = self.filtered(lambda d: d.state == "draft")
        errors = []
        for doc in drafts:
            try:
                doc.action_generate()
            except UserError as e:
                errors.append(f"{doc.employee_id.name}: {e.args[0]}")
        if errors:
            raise UserError("Some documents failed:\n" + "\n".join(errors))

    def action_bulk_archive(self):
        """Archive selected documents."""
        archivable = self.filtered(lambda d: d.state not in ("archived", "draft"))
        archivable.write({"state": "archived"})
