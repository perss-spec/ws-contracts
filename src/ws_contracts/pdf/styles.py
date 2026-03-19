"""Color palettes, font settings, and dimensions for PDF generation."""

from __future__ import annotations


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ── NDA Palette (red/gold theme) ──

NDA_PALETTE = {
    "DARK_RED":       "#1A0000",
    "CRIMSON":        "#8B0000",
    "RED_ACCENT":     "#C62828",
    "DEEP_RED":       "#7B1A1A",
    "GOLD":           "#B8860B",
    "GOLD_LIGHT":     "#D4A017",
    "TEXT_PRIMARY":   "#1A1A1A",
    "TEXT_SECONDARY": "#4A4A4A",
    "TEXT_MUTED":     "#6B6B6B",
    "LIGHT_GRAY":     "#D0D0D0",
    "RED_TINT":       "#FDF2F2",
    "WHITE":          "#FFFFFF",
    "PARTY_BG":       "#FBF5F5",
}

# ── Contract Palette (navy/cyan theme) ──

CONTRACT_PALETTE = {
    "NAVY":           "#0A0E17",
    "DARK":           "#0D1117",
    "CYAN":           "#00BCD4",
    "CYAN_DARK":      "#0097A7",
    "TEXT_PRIMARY":   "#1A1A1A",
    "TEXT_SECONDARY": "#4A4A4A",
    "TEXT_MUTED":     "#6B6B6B",
    "LIGHT_GRAY":     "#D0D0D0",
    "CYAN_TINT":      "#E8F5F7",
    "WHITE":          "#FFFFFF",
    "FAFBFC":         "#FAFBFC",
}

# ── Font names (must match add_font calls) ──

FONTS = {
    "BODY": "Cambria",
    "HEADING": "Calibri",
}

# ── A4 Dimensions (mm) ──

DIMS = {
    "PAGE_W": 210.0,
    "PAGE_H": 297.0,
    "MARGIN_LEFT": 18.0,
    "MARGIN_RIGHT": 18.0,
    "MARGIN_TOP": 20.0,
    "MARGIN_BOTTOM": 20.0,
    "HEADER_H": 15.0,
    "FOOTER_H": 20.0,
    "CONTENT_W": 174.0,   # 210 - 18 - 18
    "CONTENT_TOP": 17.0,  # after header
    "CONTENT_BOTTOM": 277.0,  # before footer
}

NDA_TERM_YEARS = 5
CONTRACT_END_DATE = "31.12.2026"
TAX_RATE = 0.06
TERMINATION_NOTICE_DAYS = 30
