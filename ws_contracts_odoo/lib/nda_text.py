"""NDA section texts and rendering — all 12 sections."""

from __future__ import annotations

# Re-use helpers from pdf_generators
from .pdf_generators import (
    _sec_heading, _body, _sub, _page_break,
    set_color, ML, CW, CB, BODY_FONT, HEAD_FONT,
    NDA_TERM_YEARS, _num_word_short, fmt_date,
)


# ── Section data ──

DEFINITIONS = [
    ("1.1", "\u201cCompany\u201d shall mean Woodenshark LLC, as the Disclosing Party under this Agreement."),
    ("1.2", "\u201cConfidential Information\u201d shall mean any and all non-public, proprietary, or trade secret information, whether in oral, written, electronic, visual, or any other form, that is disclosed by or on behalf of the Company to the Receiving Party, including but not limited to the categories set forth in Section 2."),
    ("1.3", "\u201cReceiving Party\u201d shall mean the Party receiving Confidential Information."),
    ("1.4", "\u201cRepresentatives\u201d shall mean officers, directors, employees, agents, contractors, advisors, attorneys, and accountants who have a legitimate need to know the Confidential Information and who are bound by obligations of confidentiality no less restrictive than those set forth herein."),
    ("1.5", "\u201cPurpose\u201d shall mean the evaluation, performance, and administration of the Consulting Agreement, including research, design, development, engineering, testing, and production of UAV systems, Radio-Electronic Warfare systems, embedded firmware, flight control systems, and related defense technologies."),
    ("1.6", "\u201cMaterials\u201d shall mean all tangible and intangible embodiments of Confidential Information, including documents, drawings, schematics, prototypes, source code, firmware, datasets, reports, and any copies or derivatives thereof."),
    ("1.7", "\u201cTrade Secrets\u201d shall mean any information that derives independent economic value from not being generally known to or readily ascertainable by other persons, and is the subject of reasonable efforts to maintain its secrecy, as defined under the Delaware Uniform Trade Secrets Act and the Defend Trade Secrets Act of 2016."),
]

CONFIDENTIAL_INFO_INTRO = "Confidential Information includes, without limitation, the following categories:"

CONFIDENTIAL_INFO_ITEMS = [
    ("(a)", "Technical Information: designs, drawings, engineering specifications, schematics, PCB layouts, CAD/CAM files, algorithms, formulas, processes, inventions, research data, test data, flight test logs, telemetry data, and technical know-how;"),
    ("(b)", "Software and Firmware: source code, object code, firmware images, APIs, communication protocols, encryption keys, flight control algorithms, navigation algorithms, and related documentation;"),
    ("(c)", "Product Information: prototypes, product specifications, product roadmaps, production processes, manufacturing techniques, bill of materials, and supply chain data;"),
    ("(d)", "Business Information: business plans, strategies, pricing, financial data, customer lists, supplier lists, contract terms, and partnership discussions;"),
    ("(e)", "Defense and Military Information: information related to defense applications, military specifications, electronic warfare parameters, frequency data, signal characteristics, and any information subject to export control regulations including ITAR and EAR;"),
    ("(f)", "Intellectual Property: patent applications, invention disclosures, trade secrets, trademarks, copyrights, and any other proprietary rights."),
]

CONFIDENTIAL_INFO_CLOSING = "Confidential Information need not be marked as \u201cconfidential\u201d to be protected under this Agreement. Information disclosed orally shall be considered Confidential Information if it would reasonably be understood to be confidential given the nature of the information and the circumstances of disclosure."

OBLIGATIONS = [
    ("3.1", "The Receiving Party shall not, without the prior written consent of the Disclosing Party, disclose, publish, or otherwise make available any Confidential Information to any third party, except to its Representatives in accordance with this Agreement."),
    ("3.2", "The Receiving Party shall protect the Confidential Information using at least the same degree of care that it uses to protect its own confidential information, but in no event less than a reasonable degree of care."),
    ("3.3", "The Receiving Party shall use the Confidential Information solely for the Purpose and shall not use it for any other purpose, including reverse engineering, competitive analysis, or development of competing products."),
    ("3.4", "The Receiving Party shall not reverse engineer, disassemble, decompile, or otherwise attempt to derive the composition, structure, or underlying ideas of any Confidential Information, including prototypes, hardware, software, or firmware."),
    ("3.5", "The Receiving Party shall use encrypted communications when transmitting Confidential Information electronically, use strong passwords and multi-factor authentication, and not store Confidential Information on unsecured personal devices or public cloud services without prior written consent."),
    ("3.6", "The Receiving Party shall promptly notify the Disclosing Party in writing of any actual or suspected unauthorized access, disclosure, or loss of Confidential Information."),
    ("3.7", "If the Receiving Party becomes legally compelled by judicial or administrative order, subpoena, or other legal process to disclose any Confidential Information, the Receiving Party shall: (i) provide the Disclosing Party with prompt written notice, to the extent legally permitted, so that the Disclosing Party may seek a protective order or other appropriate remedy; (ii) cooperate with the Disclosing Party in seeking such protective measures; and (iii) disclose only the minimum portion of Confidential Information that is legally required."),
]

EXCLUSIONS_INTRO = "The obligations of confidentiality shall not apply to information that the Receiving Party can demonstrate by clear and convincing evidence:"

EXCLUSIONS_ITEMS = [
    ("(a)", "was already in the public domain at the time of disclosure through no fault of the Receiving Party;"),
    ("(b)", "becomes publicly available after disclosure through no fault of the Receiving Party;"),
    ("(c)", "was rightfully in the Receiving Party\u2019s possession prior to disclosure, as documented by contemporaneous written records;"),
    ("(d)", "is rightfully obtained from a third party without obligation of confidentiality;"),
    ("(e)", "is independently developed without reference to or use of the Confidential Information."),
]

RETURN_MATERIALS = [
    ("6.1", "Upon expiration, termination, or written request, the Receiving Party shall promptly return or destroy all Materials containing Confidential Information and provide written certification of destruction within fifteen (15) business days."),
    ("6.2", "For electronically stored Confidential Information, the Receiving Party shall employ secure deletion methods (multi-pass overwrite, degaussing, or physical destruction of storage media)."),
    ("6.3", "The Receiving Party may retain one archival copy solely for compliance with applicable law, provided it remains subject to all confidentiality obligations."),
]

REMEDIES_CALLOUT = "The Parties acknowledge that any breach may cause irreparable injury for which monetary damages would be inadequate. The Disclosing Party shall be entitled to seek immediate injunctive relief without the necessity of proving actual damages or posting a bond."

REMEDIES = [
    ("7.1", "The rights and remedies are cumulative and in addition to any other rights available at law or in equity, including claims for damages, an accounting of profits, and recovery of attorneys\u2019 fees."),
    ("7.2", "The Receiving Party shall indemnify and hold harmless the Disclosing Party from all claims, damages, losses, and expenses arising from any breach of this Agreement."),
]

NON_SOLICITATION = "During the term and for two (2) years following termination, the Receiving Party shall not use Confidential Information to directly or indirectly solicit, recruit, or hire any employee, contractor, or key personnel of the Company, or to solicit or divert any client, customer, supplier, or business partner of the Company."

INTELLECTUAL_PROPERTY = [
    ("9.1", "Nothing in this Agreement grants the Receiving Party any right, title, or interest in the Confidential Information or any intellectual property of the Disclosing Party."),
    ("9.2", "Any inventions or work product created using the Company\u2019s Confidential Information shall be governed by the Consulting Agreement and shall be the sole property of the Company."),
    ("9.3", "ALL CONFIDENTIAL INFORMATION IS PROVIDED \u201cAS IS.\u201d NEITHER PARTY MAKES ANY WARRANTY WITH RESPECT TO THE ACCURACY, COMPLETENESS, OR FITNESS FOR A PARTICULAR PURPOSE OF ANY CONFIDENTIAL INFORMATION."),
]

GOVERNING_LAW = [
    ("10.1", "This Agreement shall be governed by the laws of the State of Delaware, without regard to conflict of laws principles."),
    ("10.2", "The Parties submit to the exclusive jurisdiction of the courts of the State of Delaware. Each Party waives any objection to venue."),
    ("10.3", "In any action to enforce this Agreement, the prevailing Party shall be entitled to recover reasonable attorneys\u2019 fees and costs."),
]

GENERAL_PROVISIONS = [
    ("11.1", "All notices shall be in writing, delivered personally, by registered mail, or by recognized courier service to the addresses set forth herein."),
    ("11.2", "Neither Party may assign this Agreement without prior written consent, except that the Company may assign to a successor entity in connection with a merger or acquisition."),
    ("11.3", "No failure or delay in exercising any right shall operate as a waiver thereof."),
    ("11.4", "If any provision is held invalid, it shall be modified to the minimum extent necessary; the remaining provisions shall continue in full force."),
    ("11.5", "This Agreement may not be amended except by a written instrument signed by all Parties."),
    ("11.6", "The Receiving Party acknowledges that certain Confidential Information may be subject to ITAR and EAR export control regulations and agrees to comply with all applicable export control laws."),
    ("11.7", "No Party shall issue any public disclosure regarding this Agreement without the prior written consent of the other Parties."),
    ("11.8", "This Agreement may be executed in counterparts, each of which shall be deemed an original and all of which together shall constitute one and the same instrument. Electronic signatures and PDF copies shall be deemed originals for all purposes."),
]

ENTIRE_AGREEMENT_TEMPLATE = "This Agreement, together with the Consulting Agreement dated {effective_date}, constitutes the entire agreement between the Parties with respect to the subject matter hereof. In the event of any conflict regarding Confidential Information, the more restrictive provision shall prevail."


def _callout_box(pdf, text, C):
    _page_break(pdf, 20)
    y = pdf.get_y()
    set_color(pdf, C["RED_TINT"], "fill")
    set_color(pdf, C["RED_ACCENT"], "draw")
    pdf.set_line_width(0.8)
    pdf.rect(ML, y, CW, 20, style="DF")
    set_color(pdf, C["RED_ACCENT"], "fill")
    pdf.rect(ML, y, 1.2, 20, style="F")
    pdf.set_xy(ML + 4, y + 3)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.multi_cell(CW - 8, 5, text, align="J")
    pdf.set_y(y + 22)


def render_sections(pdf, ed, C):
    """Render all 12 NDA sections into the pdf. ed = formatted effective date string."""
    accent = C["CRIMSON"]
    sub_accent = C["RED_ACCENT"]

    # 1. DEFINITIONS
    _sec_heading(pdf, "1. DEFINITIONS", accent)
    for num, text in DEFINITIONS:
        _sub(pdf, num, text, sub_accent)

    # 2. CONFIDENTIAL INFORMATION
    _sec_heading(pdf, "2. CONFIDENTIAL INFORMATION", accent)
    _body(pdf, CONFIDENTIAL_INFO_INTRO)
    for num, text in CONFIDENTIAL_INFO_ITEMS:
        _sub(pdf, num, text, sub_accent)
    _body(pdf, CONFIDENTIAL_INFO_CLOSING)

    # 3. OBLIGATIONS OF RECEIVING PARTY
    _sec_heading(pdf, "3. OBLIGATIONS OF RECEIVING PARTY", accent)
    for num, text in OBLIGATIONS:
        _sub(pdf, num, text, sub_accent)

    # 4. EXCLUSIONS FROM CONFIDENTIAL INFORMATION
    _sec_heading(pdf, "4. EXCLUSIONS FROM CONFIDENTIAL INFORMATION", accent)
    _body(pdf, EXCLUSIONS_INTRO)
    for num, text in EXCLUSIONS_ITEMS:
        _sub(pdf, num, text, sub_accent)

    # 5. TERM AND TERMINATION
    _sec_heading(pdf, "5. TERM AND TERMINATION", accent)
    years = NDA_TERM_YEARS
    word = _num_word_short(years)
    term_paras = [
        ("5.1", f"This Agreement shall commence on the Effective Date and shall remain in full force and effect for a period of {word} ({years}) years, unless earlier terminated."),
        ("5.2", "Either Party may terminate this Agreement by providing thirty (30) days\u2019 prior written notice."),
        ("5.3", f"The obligations of confidentiality shall survive for a period of {word} ({years}) years following expiration or termination. With respect to Trade Secrets, the obligations shall survive for as long as such information remains a Trade Secret."),
        ("5.4", "Upon termination, the Receiving Party shall immediately cease all use of the Confidential Information and comply with the return obligations set forth in Section 6."),
    ]
    for num, text in term_paras:
        _sub(pdf, num, text, sub_accent)

    # 6. RETURN OF MATERIALS
    _sec_heading(pdf, "6. RETURN OF MATERIALS", accent)
    for num, text in RETURN_MATERIALS:
        _sub(pdf, num, text, sub_accent)

    # 7. REMEDIES
    _sec_heading(pdf, "7. REMEDIES", accent)
    _callout_box(pdf, REMEDIES_CALLOUT, C)
    for num, text in REMEDIES:
        _sub(pdf, num, text, sub_accent)

    # 8. NON-SOLICITATION
    _sec_heading(pdf, "8. NON-SOLICITATION", accent)
    _body(pdf, NON_SOLICITATION)

    # 9. INTELLECTUAL PROPERTY
    _sec_heading(pdf, "9. INTELLECTUAL PROPERTY", accent)
    for num, text in INTELLECTUAL_PROPERTY:
        _sub(pdf, num, text, sub_accent)

    # 10. GOVERNING LAW AND JURISDICTION
    _sec_heading(pdf, "10. GOVERNING LAW AND JURISDICTION", accent)
    for num, text in GOVERNING_LAW:
        _sub(pdf, num, text, sub_accent)

    # 11. GENERAL PROVISIONS
    _sec_heading(pdf, "11. GENERAL PROVISIONS", accent)
    for num, text in GENERAL_PROVISIONS:
        _sub(pdf, num, text, sub_accent)

    # 12. ENTIRE AGREEMENT
    _sec_heading(pdf, "12. ENTIRE AGREEMENT", accent)
    _body(pdf, ENTIRE_AGREEMENT_TEMPLATE.format(effective_date=ed))
