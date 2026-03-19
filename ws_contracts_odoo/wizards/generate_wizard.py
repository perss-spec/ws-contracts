import base64
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


class GenerateWizard(models.TransientModel):
    _name = "ws.generate.wizard"
    _description = "Generate NDA / Contract PDF"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    doc_type = fields.Selection(
        [("nda", "NDA"), ("contract", "Consulting Agreement"), ("both", "Both")],
        string="Document Type",
        default="both",
        required=True,
    )

    # v2: template-based generation
    use_template = fields.Boolean("Use Template", default=False)
    template_id = fields.Many2one(
        "ws.contract.template", string="Template",
        domain="[('company_id', '=', employee_company_id)]",
    )
    employee_company_id = fields.Many2one(
        related="employee_id.company_id", readonly=True,
    )

    # Output fields for download
    nda_file = fields.Binary("NDA PDF", readonly=True)
    nda_filename = fields.Char("NDA Filename", readonly=True)
    contract_file = fields.Binary("Contract PDF", readonly=True)
    contract_filename = fields.Char("Contract Filename", readonly=True)
    docx_file = fields.Binary("DOCX File", readonly=True)
    docx_filename = fields.Char("DOCX Filename", readonly=True)
    state = fields.Selection(
        [("choose", "Choose"), ("done", "Done")],
        default="choose",
    )

    def action_generate(self):
        self.ensure_one()
        emp = self.employee_id
        data = emp._get_contract_data()

        from ..lib.pdf_generators import generate_nda, generate_contract, EmployeeData

        emp_data = EmployeeData(**data)
        vals = {"state": "done"}

        if self.use_template:
            if not self.template_id:
                raise UserError("Please select a template.")
            self._generate_from_template(emp_data, vals)
        else:
            self._generate_legacy(emp_data, vals)

        self.write(vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "ws.generate.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _generate_from_template(self, emp_data, vals):
        """Generate PDF from selected template (v2 flow)."""
        from ..lib.pdf_generators import generate_nda, generate_contract

        tmpl = self.template_id
        tmpl_data = tmpl.to_template_data()

        # DOCX generation path
        if tmpl.generation_method == "docx":
            self._generate_from_docx_template(tmpl, vals)
            return

        if tmpl_data.doc_type == "nda":
            missing = emp_data.validate_for_nda()
            if missing:
                raise UserError(f"NDA: missing fields — {', '.join(missing)}")
            pdf_bytes, filename = generate_nda(emp_data, FONTS_DIR, template=tmpl_data)
            vals["nda_file"] = base64.b64encode(pdf_bytes)
            vals["nda_filename"] = filename
        else:
            missing = emp_data.validate_for_contract()
            if missing:
                raise UserError(f"Contract: missing fields — {', '.join(missing)}")
            pdf_bytes, filename = generate_contract(emp_data, FONTS_DIR, template=tmpl_data)
            vals["contract_file"] = base64.b64encode(pdf_bytes)
            vals["contract_filename"] = filename

        # Save attachment + create document record
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(pdf_bytes),
            "res_model": "hr.employee",
            "res_id": self.employee_id.id,
            "mimetype": "application/pdf",
        })

        self.env["ws.contract.document"].create({
            "employee_id": self.employee_id.id,
            "template_id": tmpl.id,
            "state": "generated",
            "pdf_attachment_id": attachment.id,
            "generated_date": fields.Datetime.now(),
        })

    def _generate_from_docx_template(self, template, vals):
        """Generate DOCX from template with placeholders."""
        if not template.docx_template:
            raise UserError("No DOCX template file uploaded on the template record.")

        from ..lib.docx_generator import fill_docx_template

        emp = self.employee_id
        placeholders = emp._get_pl_contract_data()

        # For wizard-based generation, we use minimal placeholders
        # Full placeholder data should be set on the document record

        docx_bytes = fill_docx_template(
            base64.b64decode(template.docx_template),
            placeholders,
        )

        filename = f"{template.doc_title or 'Document'}_{emp.name}.docx"
        filename = filename.replace(" ", "_")

        vals["docx_file"] = base64.b64encode(docx_bytes)
        vals["docx_filename"] = filename

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(docx_bytes),
            "res_model": "hr.employee",
            "res_id": emp.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        })

        self.env["ws.contract.document"].create({
            "employee_id": emp.id,
            "template_id": template.id,
            "state": "generated",
            "pdf_attachment_id": attachment.id,
            "generated_date": fields.Datetime.now(),
        })

    def _generate_legacy(self, emp_data, vals):
        """Generate PDF using legacy hardcoded flow (backward compat)."""
        from ..lib.pdf_generators import generate_nda, generate_contract

        if self.doc_type in ("nda", "both"):
            missing = emp_data.validate_for_nda()
            if missing:
                raise UserError(f"NDA: missing fields — {', '.join(missing)}")
            nda_bytes, nda_name = generate_nda(emp_data, FONTS_DIR)
            vals["nda_file"] = base64.b64encode(nda_bytes)
            vals["nda_filename"] = nda_name
            self.env["ir.attachment"].create({
                "name": nda_name,
                "type": "binary",
                "datas": base64.b64encode(nda_bytes),
                "res_model": "hr.employee",
                "res_id": self.employee_id.id,
                "mimetype": "application/pdf",
            })

        if self.doc_type in ("contract", "both"):
            missing = emp_data.validate_for_contract()
            if missing:
                raise UserError(f"Contract: missing fields — {', '.join(missing)}")
            contract_bytes, contract_name = generate_contract(emp_data, FONTS_DIR)
            vals["contract_file"] = base64.b64encode(contract_bytes)
            vals["contract_filename"] = contract_name
            self.env["ir.attachment"].create({
                "name": contract_name,
                "type": "binary",
                "datas": base64.b64encode(contract_bytes),
                "res_model": "hr.employee",
                "res_id": self.employee_id.id,
                "mimetype": "application/pdf",
            })
