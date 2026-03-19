{
    "name": "WS Contracts — Multi-Company Bilingual Contract System",
    "version": "18.0.2.0.0",
    "category": "Human Resources",
    "summary": "Generate bilingual NDA and Contract PDFs with multi-company support and Odoo Sign integration",
    "description": """
        Multi-company bilingual contract management system:
        - Contract templates with company branding
        - Bilingual PDF generation (EN + local language)
        - NDA, Consulting Agreement, and custom document types
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
        "views/contract_template_views.xml",
        "views/contract_document_views.xml",
        "views/generate_wizard_views.xml",
        "views/hr_employee_views.xml",
        "data/nda_template_ws.xml",
        "data/contract_template_ws.xml",
        "data/cron.xml",
    ],
    "external_dependencies": {
        "python": ["fpdf2"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
