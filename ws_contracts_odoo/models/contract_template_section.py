import json
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ContractTemplateSection(models.Model):
    _name = "ws.contract.template.section"
    _description = "Contract Template Section"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "ws.contract.template", string="Template",
        required=True, ondelete="cascade",
    )
    sequence = fields.Integer("Sequence", default=10)
    title_en = fields.Char("Title (EN)", required=True)
    title_local = fields.Char("Title (Local)")

    # JSON content fields
    # Format: [{"type": "paragraph", "text": "..."}, {"type": "bullet", "label": "1.1", "text": "..."}]
    content_en = fields.Text("Content EN (JSON)", default="[]")
    content_local = fields.Text("Content Local (JSON)", default="[]")

    style = fields.Selection(
        [("normal", "Normal"), ("callout", "Callout"), ("notice", "Notice")],
        string="Style",
        default="normal",
    )

    def to_section_data(self):
        """Convert Odoo record to SectionData for PDF generation."""
        self.ensure_one()
        from ..lib.theme import SectionData

        content_en = []
        content_local = None

        if self.content_en:
            try:
                content_en = json.loads(self.content_en)
            except (json.JSONDecodeError, TypeError):
                content_en = [{"type": "paragraph", "text": self.content_en}]

        if self.content_local:
            try:
                content_local = json.loads(self.content_local)
            except (json.JSONDecodeError, TypeError):
                content_local = [{"type": "paragraph", "text": self.content_local}]

        return SectionData(
            sequence=self.sequence,
            title_en=self.title_en or "",
            title_local=self.title_local or None,
            content_en=content_en,
            content_local=content_local,
            style=self.style or "normal",
        )
