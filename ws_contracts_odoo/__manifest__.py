{
    "name": "WS Contracts — NDA & Consulting Agreement Generator",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Generate NDA and Consulting Agreement PDFs from employee cards",
    "description": """
        Adds a "Generate Documents" button to the employee form.
        Generates branded NDA and Consulting Agreement PDFs with:
        - AES-256 encryption
        - Watermarks
        - Corporate branding (Woodenshark LLC)
        - Auto-save to employee attachments
    """,
    "author": "Woodenshark LLC",
    "website": "https://woodenshark.com",
    "license": "LGPL-3",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/generate_wizard_views.xml",
        "views/hr_employee_views.xml",
    ],
    "external_dependencies": {
        "python": ["fpdf2"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
