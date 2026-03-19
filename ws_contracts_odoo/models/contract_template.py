import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

PL_CONTRACT_TYPES = {"probna_1m", "probna_2m", "probna_3m", "probna_2plus1",
                     "zlecenie", "czas_okreslony", "czas_nieokreslony"}


class ContractTemplate(models.Model):
    _name = "ws.contract.template"
    _description = "Contract Template"
    _order = "company_id, doc_type, name"

    _sql_constraints = [
        ("unique_name_company", "UNIQUE(name, company_id)",
         "Template name must be unique within a company."),
    ]

    name = fields.Char("Template Name", required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
    )
    doc_type = fields.Selection(
        [
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
        ],
        string="Document Type",
        required=True,
        default="nda",
    )
    generation_method = fields.Selection(
        [("pdf", "PDF (Sections)"), ("docx", "DOCX Template")],
        string="Generation Method", default="pdf", required=True,
    )
    active = fields.Boolean(default=True)

    # DOCX template
    docx_template = fields.Binary("DOCX Template File", attachment=True)
    docx_template_filename = fields.Char("DOCX Filename")

    # Theme / branding
    primary_color = fields.Char("Primary Color", default="#8B0000")
    accent_color = fields.Char("Accent Color", default="#D4AF37")
    watermark_text = fields.Char("Watermark Text", default="CONFIDENTIAL")
    signatory_name = fields.Char("Signatory Name")
    signatory_title = fields.Char("Signatory Title")
    signatory_email = fields.Char("Signatory Email")
    company_address = fields.Text("Company Address (for PDF)")
    company_address_flat = fields.Char("Company Address (flat)",
                                      help="One-line address for PDF footer")

    # Local language for bilingual docs
    local_lang = fields.Selection(
        [("none", "English only"), ("pl", "Polish"), ("uk", "Ukrainian")],
        string="Local Language",
        default="none",
        help="Adds bilingual text (italic, smaller font) below English content",
    )

    # Document-specific settings
    nda_term_years = fields.Integer("NDA Term (years)", default=5)
    contract_end_date = fields.Date("Contract End Date")
    tax_rate = fields.Float("Tax Rate", default=0.06, digits=(5, 4),
                            help="Decimal rate, e.g. 0.06 = 6%")
    termination_notice_days = fields.Integer("Termination Notice (days)", default=30)

    # Bank details
    bank_swift = fields.Char("SWIFT")
    bank_account = fields.Char("Account Number")
    bank_name = fields.Char("Bank Name")

    # Sections
    section_ids = fields.One2many(
        "ws.contract.template.section", "template_id",
        string="Sections", copy=True,
    )

    # Classification
    classification_label = fields.Char("Classification Label", default="STRICTLY CONFIDENTIAL",
                                       help="Shown in PDF header, e.g. STRICTLY CONFIDENTIAL")

    # Header
    header_label = fields.Char(
        "Header Label",
        default="STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED",
    )

    doc_title = fields.Char("Document Title", compute="_compute_doc_title", store=True)
    doc_subtitle = fields.Char("Document Subtitle")

    @api.depends("doc_type")
    def _compute_doc_title(self):
        titles = {
            "nda": "Non-Disclosure Agreement",
            "contract": "Consulting Agreement",
            "nca": "Non-Compete Agreement",
            "employment": "Employment Contract",
            "b2b": "B2B Contract",
            "probna_1m": "Probationary Contract (1m)",
            "probna_2m": "Probationary Contract (2m)",
            "probna_3m": "Probationary Contract (3m)",
            "probna_2plus1": "Probationary Contract (2+1)",
            "zlecenie": "Civil Law Contract",
            "czas_okreslony": "Fixed-Term Employment Contract",
            "czas_nieokreslony": "Indefinite Employment Contract",
        }
        for rec in self:
            rec.doc_title = titles.get(rec.doc_type, "Document")

    def to_template_data(self):
        """Convert Odoo record to TemplateData for PDF generation."""
        self.ensure_one()
        from ..lib.theme import CompanyTheme, SectionData, TemplateData, NDA_PALETTE, CONTRACT_PALETTE

        theme = CompanyTheme(
            company_name=self.company_id.name or "",
            company_address=self.company_address or "",
            company_address_flat=self.company_address_flat or "",
            primary_color=self.primary_color or "#8B0000",
            accent_color=self.accent_color or "#D4AF37",
            watermark_text=self.watermark_text or "CONFIDENTIAL",
            signatory_name=self.signatory_name or "",
            signatory_title=self.signatory_title or "",
            signatory_email=self.signatory_email or "",
            local_lang=self.local_lang if self.local_lang != "none" else None,
            bank_swift=self.bank_swift or "",
            bank_account=self.bank_account or "",
            bank_name=self.bank_name or "",
        )

        sections = []
        for sec in self.section_ids.sorted("sequence"):
            sections.append(sec.to_section_data())

        palette = NDA_PALETTE if self.doc_type == "nda" else CONTRACT_PALETTE

        end_date = ""
        if self.contract_end_date:
            end_date = self.contract_end_date.strftime("%d.%m.%Y")

        return TemplateData(
            doc_type=self.doc_type,
            doc_title=self.doc_title or "Document",
            doc_subtitle=self.doc_subtitle or "",
            theme=theme,
            sections=sections,
            palette=palette,
            nda_term_years=self.nda_term_years or 5,
            contract_end_date=end_date,
            tax_rate=self.tax_rate or 0.06,
            termination_notice_days=self.termination_notice_days or 30,
            classification_label=self.classification_label or "STRICTLY CONFIDENTIAL",
            header_label=self.header_label or "",
        )
