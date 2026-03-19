import base64
import calendar
import logging
from datetime import date
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

# Decision tree: contract_category + conditions → doc_type
CATEGORY_TO_DOC_TYPE = {
    "civil_law_pl": "zlecenie",
    "consulting_en": "contract",
    "b2b": "b2b",
}

PROBATION_MAP = {
    "lt6": "probna_1m",
    "6to12": "probna_2m",
    "12plus": "probna_3m",
}


class SmartContractWizard(models.TransientModel):
    _name = "ws.contract.smart.wizard"
    _description = "Smart Contract Wizard — auto-select template"

    # ── Navigation ──
    state = fields.Selection([
        ("step1_category", "Category"),
        ("step2_conditions", "Conditions"),
        ("step3_details", "Details"),
        ("step4_done", "Done"),
    ], default="step1_category", required=True)

    # ── Step 1: Category ──
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True,
    )
    employee_company_id = fields.Many2one(
        related="employee_id.company_id", readonly=True,
    )
    contract_category = fields.Selection([
        ("employment_pl", "Employment Contract (PL)"),
        ("civil_law_pl", "Civil Law / Zlecenie (PL)"),
        ("consulting_en", "Consulting Agreement (EN)"),
        ("b2b", "B2B Contract"),
    ], string="Contract Category", default="employment_pl")

    # ── Step 2: Conditions (employment_pl branch) ──
    needs_probation = fields.Boolean("Probation Period?", default=False)
    followup_duration = fields.Selection([
        ("lt6", "< 6 months"),
        ("6to12", "6–12 months"),
        ("12plus", "12+ months"),
    ], string="Planned Follow-up Duration")
    needs_extended_probation = fields.Boolean("Extended Probation (2+1)?")
    has_end_date = fields.Boolean("Fixed-Term Contract?", default=True)

    # ── Resolved template ──
    resolved_doc_type = fields.Selection([
        ("nda", "NDA"),
        ("contract", "Consulting Agreement"),
        ("nca", "Non-Compete Agreement"),
        ("employment", "Employment Contract"),
        ("b2b", "B2B Contract"),
        ("probna_1m", "Probationary ≤ 1 month"),
        ("probna_2m", "Probationary ≤ 2 months"),
        ("probna_3m", "Probationary ≤ 3 months"),
        ("probna_2plus1", "Probationary Extended (2+1)"),
        ("zlecenie", "Civil Law Contract (Mandate)"),
        ("czas_okreslony", "Fixed-Term Employment"),
        ("czas_nieokreslony", "Indefinite Employment"),
    ], compute="_compute_resolved_doc_type", store=True, readonly=True)

    resolved_template_id = fields.Many2one(
        "ws.contract.template", string="Matched Template",
        compute="_compute_resolved_template", store=True, readonly=True,
    )
    template_override_id = fields.Many2one(
        "ws.contract.template", string="Override Template",
        domain="[('company_id', '=', employee_company_id), ('active', '=', True)]",
    )

    # ── NDA ──
    include_nda = fields.Boolean("Include NDA", default=True)
    has_existing_nda = fields.Boolean(
        compute="_compute_has_existing_nda", store=True,
    )
    nda_template_id = fields.Many2one(
        "ws.contract.template", string="NDA Template",
        compute="_compute_nda_template", store=True, readonly=True,
    )

    # ── Step 3: Contract details ──
    signing_date = fields.Date("Signing Date", default=fields.Date.today)
    contract_start_date = fields.Date("Start Date")
    contract_end_date = fields.Date("End Date")
    job_title_pl = fields.Char("Job Title (PL)")
    job_title_en = fields.Char("Job Title (EN)")
    place_of_work = fields.Char("Place of Work", default="Lublin")
    working_time_pl = fields.Char("Working Time (PL)", default="pełny etat (1/1)")
    working_time_en = fields.Char("Working Time (EN)", default="full time (1/1)")
    salary_gross = fields.Float("Salary Gross (PLN/month)", digits=(10, 2))
    hourly_rate_gross = fields.Float("Hourly Rate Gross (PLN)", digits=(10, 2))
    scope_of_work_pl = fields.Text("Scope of Work (PL)")
    scope_of_work_en = fields.Text("Scope of Work (EN)")
    id_document_pl = fields.Char("ID Document (PL)")
    id_document_en = fields.Char("ID Document (EN)")
    justification_pl = fields.Text("Extension Justification (PL)")
    justification_en = fields.Text("Extension Justification (EN)")

    # ── Step 4: Result ──
    created_document_ids = fields.Many2many(
        "ws.contract.document", string="Created Documents",
    )

    # ═══════════════════════════════════════
    # Computes
    # ═══════════════════════════════════════

    @api.depends(
        "contract_category", "needs_probation", "followup_duration",
        "needs_extended_probation", "has_end_date",
    )
    def _compute_resolved_doc_type(self):
        for rec in self:
            rec.resolved_doc_type = rec._resolve_doc_type()

    def _resolve_doc_type(self):
        cat = self.contract_category
        if not cat:
            return False
        if cat != "employment_pl":
            return CATEGORY_TO_DOC_TYPE.get(cat, False)
        # Employment PL branch
        if self.needs_probation:
            dur = self.followup_duration or "lt6"
            if dur == "6to12" and self.needs_extended_probation:
                return "probna_2plus1"
            return PROBATION_MAP.get(dur, "probna_1m")
        return "czas_okreslony" if self.has_end_date else "czas_nieokreslony"

    @api.depends("resolved_doc_type", "employee_company_id")
    def _compute_resolved_template(self):
        Template = self.env["ws.contract.template"]
        for rec in self:
            if not rec.resolved_doc_type or not rec.employee_company_id:
                rec.resolved_template_id = False
                continue
            rec.resolved_template_id = Template.search([
                ("company_id", "=", rec.employee_company_id.id),
                ("doc_type", "=", rec.resolved_doc_type),
                ("active", "=", True),
            ], limit=1)

    @api.depends("employee_id.ws_document_ids.doc_type", "employee_id.ws_document_ids.state")
    def _compute_has_existing_nda(self):
        for rec in self:
            if not rec.employee_id:
                rec.has_existing_nda = False
                continue
            nda_docs = rec.employee_id.ws_document_ids.filtered(
                lambda d: d.doc_type == "nda" and d.state not in ("archived",)
            )
            rec.has_existing_nda = bool(nda_docs)

    @api.depends("employee_company_id")
    def _compute_nda_template(self):
        Template = self.env["ws.contract.template"]
        for rec in self:
            if not rec.employee_company_id:
                rec.nda_template_id = False
                continue
            rec.nda_template_id = Template.search([
                ("company_id", "=", rec.employee_company_id.id),
                ("doc_type", "=", "nda"),
                ("active", "=", True),
            ], limit=1)

    # ═══════════════════════════════════════
    # Onchange
    # ═══════════════════════════════════════

    @api.onchange("contract_category")
    def _onchange_category(self):
        self.needs_probation = False
        self.followup_duration = False
        self.needs_extended_probation = False
        self.has_end_date = True

    @api.onchange("needs_probation")
    def _onchange_needs_probation(self):
        if not self.needs_probation:
            self.followup_duration = False
            self.needs_extended_probation = False

    @api.onchange("has_existing_nda")
    def _onchange_has_existing_nda(self):
        if self.has_existing_nda:
            self.include_nda = False

    # ═══════════════════════════════════════
    # Navigation
    # ═══════════════════════════════════════

    STEP_ORDER = [
        "step1_category", "step2_conditions",
        "step3_details", "step4_done",
    ]

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_next(self):
        self.ensure_one()
        idx = self.STEP_ORDER.index(self.state)
        if self.state == "step2_conditions":
            self._validate_step2()
        if self.state == "step3_details":
            return self.action_generate_all()
        if idx < len(self.STEP_ORDER) - 1:
            self.state = self.STEP_ORDER[idx + 1]
        return self._reopen()

    def action_prev(self):
        self.ensure_one()
        idx = self.STEP_ORDER.index(self.state)
        if idx > 0:
            self.state = self.STEP_ORDER[idx - 1]
        return self._reopen()

    # ═══════════════════════════════════════
    # Validation
    # ═══════════════════════════════════════

    def _validate_step2(self):
        tmpl = self.template_override_id or self.resolved_template_id
        if not tmpl:
            raise UserError(
                f"No template found for doc_type='{self.resolved_doc_type}' "
                f"in company '{self.employee_company_id.name}'. "
                "Please create one in Contracts → Templates."
            )
        if self.include_nda and not self.nda_template_id:
            raise UserError(
                f"No NDA template found for company '{self.employee_company_id.name}'. "
                "Please create one or uncheck 'Include NDA'."
            )

    def _validate_step3(self):
        if self.signing_date and self.contract_start_date:
            if self.signing_date > self.contract_start_date:
                raise ValidationError(
                    "Signing date must be on or before contract start date."
                )
        if self.contract_end_date:
            self._validate_end_of_month(self.contract_end_date)
        # Duplicate draft check
        tmpl = self.template_override_id or self.resolved_template_id
        existing = self.env["ws.contract.document"].search([
            ("employee_id", "=", self.employee_id.id),
            ("template_id", "=", tmpl.id),
            ("state", "=", "draft"),
        ], limit=1)
        if existing:
            _logger.warning(
                "Employee %s already has draft document for template %s",
                self.employee_id.name, tmpl.name,
            )

    @staticmethod
    def _validate_end_of_month(dt):
        if not dt:
            return
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        if dt.day != last_day:
            raise ValidationError(
                f"Contract end date ({dt}) must be the last day of the month "
                f"(expected {dt.year}-{dt.month:02d}-{last_day:02d}). "
                "This is required by Polish Labour Code."
            )

    # ═══════════════════════════════════════
    # Generation
    # ═══════════════════════════════════════

    def action_generate_all(self):
        self.ensure_one()
        self._validate_step3()

        tmpl = self.template_override_id or self.resolved_template_id
        created = self.env["ws.contract.document"]

        # Create main contract document
        doc = self._create_document(tmpl)
        doc.action_generate()
        created |= doc

        # NDA if requested
        if self.include_nda and self.nda_template_id and not self.has_existing_nda:
            nda_doc = self._create_document(self.nda_template_id)
            nda_doc.action_generate()
            created |= nda_doc

        self.write({
            "state": "step4_done",
            "created_document_ids": [(6, 0, created.ids)],
        })
        return self._reopen()

    def _create_document(self, template):
        vals = {
            "employee_id": self.employee_id.id,
            "template_id": template.id,
            "state": "draft",
        }
        # Add PL contract fields if applicable
        if template.doc_type in (
            "probna_1m", "probna_2m", "probna_3m", "probna_2plus1",
            "zlecenie", "czas_okreslony", "czas_nieokreslony",
        ):
            vals.update({
                "signing_date": self.signing_date,
                "contract_start_date": self.contract_start_date,
                "contract_end_date": self.contract_end_date,
                "job_title_pl": self.job_title_pl,
                "job_title_en": self.job_title_en,
                "place_of_work": self.place_of_work,
                "working_time_pl": self.working_time_pl,
                "working_time_en": self.working_time_en,
                "salary_gross": self.salary_gross,
                "hourly_rate_gross": self.hourly_rate_gross,
                "scope_of_work_pl": self.scope_of_work_pl,
                "scope_of_work_en": self.scope_of_work_en,
                "id_document_pl": self.id_document_pl,
                "id_document_en": self.id_document_en,
                "justification_pl": self.justification_pl,
                "justification_en": self.justification_en,
            })
        return self.env["ws.contract.document"].create(vals)

    def action_open_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Created Documents",
            "res_model": "ws.contract.document",
            "view_mode": "list,form",
            "domain": [("id", "in", self.created_document_ids.ids)],
            "target": "current",
        }
