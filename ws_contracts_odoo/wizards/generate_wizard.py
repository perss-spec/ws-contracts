import base64
import logging
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Fonts directory relative to this file
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
    # Output fields for download
    nda_file = fields.Binary("NDA PDF", readonly=True)
    nda_filename = fields.Char("NDA Filename", readonly=True)
    contract_file = fields.Binary("Contract PDF", readonly=True)
    contract_filename = fields.Char("Contract Filename", readonly=True)
    state = fields.Selection(
        [("choose", "Choose"), ("done", "Done")],
        default="choose",
    )

    def action_generate(self):
        self.ensure_one()
        emp = self.employee_id
        data = emp._get_contract_data()

        # Lazy import — fpdf2 might not be available at module load time
        from ..lib.pdf_generators import generate_nda, generate_contract, EmployeeData

        emp_data = EmployeeData(**data)

        vals = {"state": "done"}

        if self.doc_type in ("nda", "both"):
            missing = emp_data.validate_for_nda()
            if missing:
                raise UserError(f"NDA: missing fields — {', '.join(missing)}")
            nda_bytes, nda_name = generate_nda(emp_data, FONTS_DIR)
            vals["nda_file"] = base64.b64encode(nda_bytes)
            vals["nda_filename"] = nda_name
            # Save to attachments
            self.env["ir.attachment"].create({
                "name": nda_name,
                "type": "binary",
                "datas": base64.b64encode(nda_bytes),
                "res_model": "hr.employee",
                "res_id": emp.id,
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
                "res_id": emp.id,
                "mimetype": "application/pdf",
            })

        self.write(vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "ws.generate.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
