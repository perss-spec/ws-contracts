"""Configuration via pydantic-settings (.env / environment)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_fonts_dir() -> Path:
    """Locate the fonts/ directory relative to the package root."""
    pkg = Path(__file__).resolve().parent
    candidates = [
        pkg.parent.parent / "fonts",  # dev layout: repo/fonts
        pkg / "fonts",                 # installed with package data
    ]
    for p in candidates:
        if p.is_dir():
            return p
    return candidates[0]


class OdooSettings(BaseSettings):
    odoo_url: str = "https://omds-sh.odoo.com"
    odoo_db: str = "omds-sh"
    odoo_user: str = ""
    odoo_password: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


class PdfSettings(BaseSettings):
    pdf_owner_password_prefix: str = "WS"
    pdf_watermark_text: str = "WOODENSHARK LLC CONFIDENTIAL"
    fonts_dir: Path = _find_fonts_dir()

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
