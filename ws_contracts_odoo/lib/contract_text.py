"""Contract section texts and rendering — all 22 sections + background."""

from __future__ import annotations

from .pdf_generators import (
    _sec_heading, _body, _page_break,
    set_color, fmt_date, num_words,
    ML, CW, CB, BODY_FONT, HEAD_FONT,
    WS_NAME, WS_ADDRESS_FLAT, CONTRACT_END_DATE, TAX_RATE,
)

TERMINATION_NOTICE_DAYS = 30

BACKGROUND = [
    "The Client is of the opinion that the Consultant has the necessary qualifications, experience and abilities to provide consulting services to the Client.",
    "The Consultant agrees to provide such consulting services to the Client on the terms and conditions set out in this Agreement.",
    "This Consulting Agreement (hereinafter the \u201cAgreement\u201d) states the terms and conditions that govern the contractual agreement by and between",
]

IN_CONSIDERATION = (
    "IN CONSIDERATION OF the matters described above and of the mutual benefits and obligations "
    "set forth in this Agreement, the receipt and sufficiency of which consideration is hereby "
    "acknowledged, the Client and the Consultant (individually, the \u201cParty\u201d and collectively "
    "the \u201cParties\u201d to this Agreement) agree as follows:"
)

SECTIONS = [
    ("SERVICES PROVIDED", [
        "The Client hereby agrees to engage a Consultant to provide the Client with the following consulting services (the \u201cServices\u201d):",
        None,  # service_description callout
        "The Services will also include any other consulting tasks which the Parties may agree on. The Consultant hereby agrees to provide such Services to the Client.",
    ]),
    ("TERM OF AGREEMENT", [
        f"The term of this Agreement (the \u201cTerm\u201d) will begin on the date of this Agreement and will remain in full force and effect until {CONTRACT_END_DATE}, subject to earlier termination as provided in this Agreement. The Term may be extended with the written consent of the Parties.",
        f"In the event that either Party wishes to terminate this Agreement prior to {CONTRACT_END_DATE} that Party will be required to provide {TERMINATION_NOTICE_DAYS} days\u2019 written notice to the other Party.",
    ]),
    ("PERFORMANCE", [
        "The Parties agree to do everything necessary to ensure that the terms of this Agreement take effect.",
    ]),
    ("CURRENCY", [
        "Except as otherwise provided in this Agreement, all monetary amounts referred to in this Agreement are in USD.",
    ]),
    ("COMPENSATION", [
        None,  # compensation callout with rate calculation
        "The Client will be invoiced every month.",
        "Invoices submitted by the Consultant to the Client are due upon receipt.",
    ]),
    ("REIMBURSEMENT OF EXPENSES", [
        "The Consultant will be reimbursed all reasonable and necessary expenses incurred by the Consultant in connection with providing the Services, such as travel expenses and other related to business development expenses.",
        "All expenses must be pre-approved by the Client.",
    ]),
    ("CONFIDENTIALITY", [
        "Confidential information (the \u201cConfidential Information\u201d) refers to any data or information relating to the Client, whether business or personal, which would reasonably be considered to be private or proprietary to the Client and that is not generally known and where the release of that Confidential Information could reasonably be expected to cause harm to the Client.",
        "The Consultant agrees that they will not disclose, divulge, reveal, report or use, for any purpose, any Confidential Information which the Consultant has obtained, except as authorized by the Client or as required by law. The obligations of confidentiality will apply during the Term and will survive indefinitely upon termination of this Agreement.",
        "All written and oral information and material disclosed or provided by the Client to the Consultant under this Agreement is Confidential Information regardless of whether it was provided before or after the date of this Agreement or how it was provided to the Consultant.",
    ]),
    ("OWNERSHIP OF INTELLECTUAL PROPERTY", [
        "All intellectual property and related material, including any trade secrets, moral rights, goodwill, relevant registrations or applications for registration, and rights in any patent, copyright, trademark, trade dress, industrial design and trade name (the \u201cIntellectual Property\u201d) that is developed or produced under this Agreement, is a \u201cwork made for hire\u201d and will be the sole property of the Client. The use of the Intellectual Property by the Client will not be restricted in any manner.",
        "The Consultant may not use the Intellectual Property for any purpose other than that contracted for in this Agreement except with the written consent of the Client. The Consultant will be responsible for any and all damages resulting from the unauthorized use of the Intellectual Property.",
    ]),
    ("RETURN OF PROPERTY", [
        "Upon the expiration or termination of this Agreement, the Consultant will return to the Client any property, documentation, records, or Confidential Information which is the property of the Client.",
    ]),
    ("CAPACITY / INDEPENDENT CONTRACTOR", [
        "In providing the Services under this Agreement it is expressly agreed that the Consultant is acting as an independent contractor and not as an employee. The Consultant and the Client acknowledge that this Agreement does not create a partnership or joint venture between them, and is exclusively a contract for service. The Client is not required to pay, or make any contributions to any social security, local, state or federal tax, unemployment compensation, workers\u2019 compensation, insurance premium, profit-sharing, pension or any other employee benefit for the Consultant during the Term. The Consultant is responsible for paying, and complying with reporting requirements for, all local, state and federal taxes related to payments made to the Consultant under this Agreement.",
    ]),
    ("NOTICE", [
        "All notices, requests, demands or other communications required or permitted by the terms of this Agreement will be given in writing and delivered to the Parties at the following addresses:",
        None,  # notice addresses
        "or to such other address as either Party may from time to time notify the other, and will be deemed to be properly delivered (a) immediately upon being served personally, (b) two days after being deposited with the postal service if served by registered mail, or (c) the following day after being deposited with an overnight courier.",
    ]),
    ("INDEMNIFICATION", [
        "Except to the extent paid in settlement from any applicable insurance policies, and to the extent permitted by applicable law, each Party agrees to indemnify and hold harmless the other Party, and its respective affiliates, officers, agents, employees, and permitted successors and assigns against any and all claims, losses, damages, liabilities, penalties, punitive damages, expenses, reasonable legal fees and costs of any kind or amount whatsoever, which result from or arise out of any act or omission of the indemnifying party, its respective affiliates, officers, agents, employees, and permitted successors and assigns that occurs in connection with this Agreement. This indemnification shall survive the termination of this Agreement.",
    ]),
    ("MODIFICATION OF AGREEMENT", [
        "Any amendment or modification of this Agreement or additional obligation assumed by either Party in connection with this Agreement will only be binding if evidenced in writing signed by each Party or an authorized representative of each Party.",
    ]),
    ("TIME OF THE ESSENCE", [
        "Time is of the essence in this Agreement. No extension or variation of this Agreement will operate as a waiver of this provision.",
    ]),
    ("ASSIGNMENT", [
        "The Consultant will not voluntarily, or by operation of law, assign or otherwise transfer its obligations under this Agreement without the prior written consent of the Client.",
    ]),
    ("ENTIRE AGREEMENT", [
        "It is agreed that there is no representation, warranty, collateral agreement or condition affecting this Agreement except as expressly provided in this Agreement.",
    ]),
    ("ENUREMENT", [
        "This Agreement will enure to the benefit of and be binding on the Parties and their respective heirs, executors, administrators and permitted successors and assigns.",
    ]),
    ("TITLES / HEADINGS", [
        "Headings are inserted for the convenience of the Parties only and are not to be considered when interpreting this Agreement.",
    ]),
    ("GENDER", [
        "Words in the singular mean and include the plural and vice versa. Words in the masculine mean and include the feminine and vice versa.",
    ]),
    ("GOVERNING LAW", [
        "This Agreement will be governed by and construed in accordance with the laws of the state of Delaware.",
    ]),
    ("SEVERABILITY", [
        "In the event that any of the provisions of this Agreement are held to be invalid or unenforceable in whole or in part, all other provisions will nevertheless continue to be valid and enforceable with the invalid or unenforceable parts severed from the remainder of this Agreement.",
    ]),
    ("WAIVER", [
        "The waiver by either Party of a breach, default, delay or omission of any of the provisions of this Agreement by the other Party will not be construed as a waiver of any subsequent breach of the same or other provisions.",
    ]),
]


def _callout_box(pdf, text, C):
    """Cyan-tinted callout box for contract."""
    _page_break(pdf, 16)
    y = pdf.get_y()
    set_color(pdf, C["CYAN_TINT"], "fill")
    set_color(pdf, C["LIGHT_GRAY"], "draw")
    pdf.set_line_width(0.3)
    pdf.rect(ML, y, CW, 12, style="DF")
    set_color(pdf, C["CYAN"], "fill")
    pdf.rect(ML, y, 1.2, 12, style="F")
    pdf.set_xy(ML + 4, y + 2)
    pdf.set_font(HEAD_FONT, "B", 13)
    set_color(pdf, C["DARK"])
    pdf.cell(CW - 8, 8, text, align="C")
    pdf.set_y(y + 14)


def _notice_boxes(pdf, emp, C):
    """Notice address rows for both parties."""
    _page_break(pdf, 16)
    set_color(pdf, C["LIGHT_GRAY"], "draw")
    pdf.set_line_width(0.15)

    y = pdf.get_y()
    pdf.line(ML, y + 8, ML + CW, y + 8)
    pdf.set_xy(ML + 4, y + 1)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(60, 5, WS_NAME)
    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 5, "mitgor@woodenshark.com", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y + 10)

    y = pdf.get_y()
    pdf.line(ML, y + 8, ML + CW, y + 8)
    pdf.set_xy(ML + 4, y + 1)
    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.cell(60, 5, emp.full_name_lat or "")
    pdf.set_font(BODY_FONT, "", 11)
    set_color(pdf, C["TEXT_SECONDARY"])
    pdf.cell(0, 5, emp.work_email or emp.phone or "", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(y + 12)


def render_sections(pdf, emp, ad, ed, C):
    """Render all contract sections. ad/ed = formatted agreement/effective date strings."""
    accent = C["DARK"]

    # BACKGROUND (Section 1)
    _sec_heading(pdf, "1. BACKGROUND", accent)
    for text in BACKGROUND:
        _body(pdf, text)

    _body(
        pdf,
        f"{WS_NAME}, a company incorporated and registered in the United States of America "
        f"whose registered office is at {WS_ADDRESS_FLAT} (hereinafter the \u201cClient\u201d)"
    )

    dob = fmt_date(emp.date_of_birth)
    pi = fmt_date(emp.passport_issued)
    pe = fmt_date(emp.passport_expires)
    _body(
        pdf,
        f"{emp.full_name_lat or ''}, with the date of birth {dob}, the holder of Ukrainian Foreign Passport "
        f"\u2116 {emp.passport_number} issued on {pi} and valid till {pe}, "
        f"with the primary address of residence {emp.address or ''}"
    )

    pdf.set_font(BODY_FONT, "B", 11)
    set_color(pdf, C["TEXT_PRIMARY"])
    pdf.set_x(ML)
    pdf.multi_cell(CW, 5, IN_CONSIDERATION, align="J")
    pdf.ln(3)

    # Compensation math
    rate = emp.rate_usd
    total_with_tax = round(rate * (1 + TAX_RATE))
    rate_words = num_words(rate)
    total_words = num_words(total_with_tax)
    rate_fmt = f"{int(rate):,}"
    total_fmt = f"{total_with_tax:,}"

    # Sections 2-23
    for idx, (title, paragraphs) in enumerate(SECTIONS):
        section_num = idx + 2
        _sec_heading(pdf, f"{section_num}. {title}", accent)

        for text in paragraphs:
            if text is None:
                if title == "SERVICES PROVIDED":
                    _callout_box(pdf, emp.service_description or "UAV Systems Development Services", C)
                elif title == "NOTICE":
                    _notice_boxes(pdf, emp, C)
                elif title == "COMPENSATION":
                    _body(pdf, (
                        f"The Consultant will charge the Client for the Services at the rate of "
                        f"{rate_fmt} ({rate_words}) USD plus {int(TAX_RATE * 100)}% tax, totaling "
                        f"{total_fmt} ({total_words}) USD per month (the \u201cCompensation\u201d) "
                        f"for full time employment."
                    ))
            else:
                _body(pdf, text)
