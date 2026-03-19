"""
Company theme, section data, and template data classes for parameterized PDF generation.
Supports multi-company, multi-language (bilingual) contract documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyTheme:
    """Visual branding and company identity for PDF documents."""
    company_name: str = "Woodenshark LLC"
    company_address: str = "3411 Silverside Road, Suite 104\nWilmington, DE 19810, USA"
    company_address_flat: str = "3411 Silverside Road, Suite 104, Rodney Building, Wilmington, DE, 19810"
    primary_color: str = "#8B0000"
    accent_color: str = "#D4AF37"
    watermark_text: str = "WOODENSHARK LLC CONFIDENTIAL"
    signatory_name: str = ""
    signatory_title: str = ""
    signatory_email: str = "mitgor@woodenshark.com"
    local_lang: Optional[str] = None  # "pl", "uk", None
    # Company bank details (for contract signature block)
    bank_swift: str = "CMFGUS33"
    bank_account: str = "822000034828"
    bank_name: str = "Wise Inc"


@dataclass
class SectionData:
    """One section of a contract/NDA template."""
    sequence: int = 0
    title_en: str = ""
    title_local: Optional[str] = None
    content_en: list = field(default_factory=list)
    # content_en format: [
    #   {"type": "paragraph", "text": "..."},
    #   {"type": "bullet", "label": "1.1", "text": "..."},
    #   {"type": "callout", "text": "..."},
    #   {"type": "notice_boxes"},  # special: render notice address boxes
    #   {"type": "compensation"},  # special: render compensation calculation
    #   {"type": "service_callout"},  # special: render service description callout
    # ]
    content_local: Optional[list] = None
    style: str = "normal"  # "normal", "callout", "notice"


@dataclass
class TemplateData:
    """Complete template configuration for PDF generation."""
    doc_type: str = "nda"  # "nda", "contract", "nca", etc.
    doc_title: str = "Non-Disclosure Agreement"
    doc_subtitle: str = "Proprietary & Restricted Information Protection"
    theme: CompanyTheme = field(default_factory=CompanyTheme)
    sections: list[SectionData] = field(default_factory=list)
    nda_term_years: int = 5
    contract_end_date: str = "31.12.2026"
    tax_rate: float = 0.06
    termination_notice_days: int = 30
    # Color palettes — doc_type determines which palette to use
    palette: dict = field(default_factory=dict)
    # Classification label on title page
    classification_label: str = "STRICTLY CONFIDENTIAL"
    classification_bg_color: Optional[str] = None  # defaults to palette color
    classification_text_color: Optional[str] = None
    # Header bar config
    header_label: str = "STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED"


# ── Preset palettes ──

NDA_PALETTE = {
    "DARK_RED": "#1A0000", "CRIMSON": "#8B0000", "RED_ACCENT": "#C62828",
    "DEEP_RED": "#7B1A1A", "GOLD_LIGHT": "#D4A017",
    "TEXT_PRIMARY": "#1A1A1A", "TEXT_SECONDARY": "#4A4A4A",
    "TEXT_MUTED": "#6B6B6B", "LIGHT_GRAY": "#D0D0D0",
    "RED_TINT": "#FDF2F2", "WHITE": "#FFFFFF", "PARTY_BG": "#FBF5F5",
    # Aliases used in header/footer
    "HEADER_COLOR": "#1A0000", "ACCENT_COLOR": "#C62828",
    "HEADER_TEXT_COLOR": "#D4A017", "COMPANY_COLOR": "#8B0000",
}

CONTRACT_PALETTE = {
    "NAVY": "#0A0E17", "DARK": "#0D1117", "CYAN": "#00BCD4",
    "CYAN_DARK": "#0097A7", "TEXT_PRIMARY": "#1A1A1A",
    "TEXT_SECONDARY": "#4A4A4A", "TEXT_MUTED": "#6B6B6B",
    "LIGHT_GRAY": "#D0D0D0", "CYAN_TINT": "#E8F5F7",
    "WHITE": "#FFFFFF", "FAFBFC": "#FAFBFC",
    # Aliases
    "HEADER_COLOR": "#0A0E17", "ACCENT_COLOR": "#00BCD4",
    "HEADER_TEXT_COLOR": "#FFFFFF", "COMPANY_COLOR": "#0D1117",
}


def default_nda_template() -> TemplateData:
    """Create default Woodenshark NDA template (backward compat)."""
    return TemplateData(
        doc_type="nda",
        doc_title="Non-Disclosure Agreement",
        doc_subtitle="Proprietary & Restricted Information Protection",
        theme=CompanyTheme(),
        palette=NDA_PALETTE,
        nda_term_years=5,
        classification_label="STRICTLY CONFIDENTIAL",
        classification_bg_color="#1A0000",
        classification_text_color="#D4A017",
        header_label="STRICTLY CONFIDENTIAL  \u2014  PROPRIETARY & RESTRICTED",
    )


def default_contract_template() -> TemplateData:
    """Create default Woodenshark Contract template (backward compat)."""
    return TemplateData(
        doc_type="contract",
        doc_title="Consulting Agreement",
        doc_subtitle="Professional Services & Technical Consulting",
        theme=CompanyTheme(),
        palette=CONTRACT_PALETTE,
        contract_end_date="31.12.2026",
        tax_rate=0.06,
        termination_notice_days=30,
        classification_label="CONFIDENTIAL",
        classification_bg_color="#0A0E17",
        classification_text_color="#FFFFFF",
        header_label="CONFIDENTIAL  \u2014  WOODENSHARK LLC PROPRIETARY",
    )
