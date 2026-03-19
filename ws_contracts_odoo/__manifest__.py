{
    "name": "WS Contracts — Multi-Company Bilingual Contract System",
    "version": "18.0.2.0.0",
    "category": "Human Resources",
    "summary": "Generate bilingual contracts (PDF + DOCX) with multi-company support and Odoo Sign integration",
    "description": """
        Multi-company bilingual contract management system:
        - Contract templates with company branding
        - Bilingual PDF generation (EN + local language)
        - NDA, Consulting Agreement, and custom document types
        - Polish contract templates (Umowa zlecenie, Umowa o dzieło)
        - DOCX generation with styled bilingual formatting
        - Odoo Sign integration for digital signatures
        - AES-256 encrypted PDFs with watermarks
        - Document lifecycle tracking (draft → signed → archived)
    """,
    "author": "Woodenshark LLC",
    "website": "https://woodenshark.com",
    "license": "LGPL-3",
    "depends": ["hr", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rules.xml",
        "views/contract_template_views.xml",
        "views/contract_document_views.xml",
        "views/server_actions.xml",
        "views/smart_wizard_views.xml",
        "views/hr_employee_views.xml",
        "data/nda_template_ws.xml",
        "data/contract_template_ws.xml",
        "data/cron.xml",
    ],
    "external_dependencies": {
        "python": ["fpdf2", "docx"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
