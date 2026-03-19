# Plan: ws-contracts v2 — Multi-Company Bilingual Contract System

## Context

**Что уже работает (Phase 1 — DONE):**
- Odoo-модуль `ws_contracts_odoo` генерирует NDA + Consulting Agreement PDF для Woodenshark LLC
- 12 `x_ws_` полей созданы на hr.employee в тестовой Odoo
- fpdf2 с AES-256 encryption, watermarks, Cambria/Calibri шрифты
- 55/55 тестов CLI-пакета проходят
- GitHub: `perss-spec/ws-contracts`

**Проблема:** Всё захардкожено под одну компанию (Woodenshark LLC). В реальности:
- 9 компаний в 4 юрисдикциях (US, PL, UK, UA)
- У каждой компании свои типы контрактов
- К каждому сотруднику привязывается 1+ контрактов
- Документы должны быть **билингвальными**: EN основной + язык страны компании (мельче, курсив, серый)

**Цель:** Параметризированная система шаблонов контрактов с поддержкой мульти-компании, мульти-языка и интеграцией Odoo Sign.

## ERD — Entity Relationship Diagram

```
┌──────────────────────┐       ┌──────────────────────────────┐
│     res.company       │       │       hr.employee             │
│──────────────────────│       │──────────────────────────────│
│ id                    │◄──┐   │ id                            │
│ name                  │   │   │ name                          │
│ x_ws_primary_color    │   │   │ company_id ──────────────────►│
│ x_ws_accent_color     │   │   │ x_ws_full_name_lat            │
│ x_ws_watermark_text   │   │   │ x_ws_passport_number          │
│ x_ws_signatory_name   │   │   │ x_ws_iban / x_ws_swift        │
│ x_ws_signatory_title  │   │   │ x_ws_rate_usd                 │
│ x_ws_jurisdiction     │   │   │ ... (12 полей)                │
│ x_ws_local_lang       │   │   └──────────────┬───────────────┘
└──────────┬───────────┘   │                    │
           │               │                    │ many2many
           │               │                    ▼
           │    ┌──────────┴──────────────────────────────────┐
           │    │        ws.contract.template                   │
           │    │─────────────────────────────────────────────│
           │    │ id                                            │
           ├───►│ company_id (Many2one → res.company)           │
                │ doc_type: selection [nda, contract, nca, ...]│
                │ name: "NDA — Woodenshark LLC"                │
                │ local_lang: selection [pl, uk, none]          │
                │ primary_color: "#8B0000"                      │
                │ accent_color: "#D4AF37"                       │
                │ watermark_text: "CONFIDENTIAL"                │
                │ signatory_name / signatory_title              │
                │ company_address                               │
                │ active: bool                                  │
                │ nda_term_years: int (default 5)               │
                │ contract_end_date: date                       │
                │ tax_rate: float (default 0.06)                │
                └──────────────┬──────────────────────────────┘
                               │ one2many
                               ▼
                ┌─────────────────────────────────────────────┐
                │     ws.contract.template.section              │
                │─────────────────────────────────────────────│
                │ id                                            │
                │ template_id (Many2one)                        │
                │ sequence: int                                 │
                │ title_en: char                                │
                │ title_local: char (nullable)                  │
                │ content_en: text (JSON — paragraphs/bullets) │
                │ content_local: text (JSON)                    │
                │ style: selection [normal, callout, notice]    │
                └─────────────────────────────────────────────┘

                ┌─────────────────────────────────────────────┐
                │     ws.contract.document                      │
                │─────────────────────────────────────────────│
                │ id                                            │
                │ employee_id (Many2one → hr.employee)          │
                │ template_id (Many2one → ws.contract.template) │
                │ state: [draft, generated, signed, archived]   │
                │ pdf_attachment_id (Many2one → ir.attachment)   │
                │ sign_request_id (Many2one → sign.request)     │
                │ generated_date: datetime                      │
                │ signed_date: datetime                         │
                └─────────────────────────────────────────────┘
```

## Билингвальный дизайн PDF

```
┌─────────────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  ← color bar (primary_color)
│                                              │
│  SECTION 3. CONFIDENTIAL INFORMATION         │  ← Cambria Bold 13pt, primary_color
│  3. ІНФОРМАЦІЯ КОНФІДЕНЦІЙНОГО ХАРАКТЕРУ     │  ← Cambria Italic 10pt, #888888
│                                              │
│  The Receiving Party agrees to hold...        │  ← Calibri 11pt, #333333
│  paragraph of English text continues here     │
│  with full legal language.                    │
│                                              │
│  Сторона-отримувач зобов'язується            │  ← Calibri Italic 9.5pt, #777777
│  зберігати конфіденційну інформацію...       │
│                                              │
│  ─────────────────────────────────────────── │  ← thin separator #CCCCCC
│                                              │
│  SECTION 4. OBLIGATIONS                       │
│  4. ЗОБОВ'ЯЗАННЯ                             │
│  ...                                         │
└─────────────────────────────────────────────┘
```

## Компании и юрисдикции

| Компания | Юрисдикция | Язык | Типы документов |
|----------|-----------|------|-----------------|
| Woodenshark LLC | US/DE | none | NDA, Consulting Agreement |
| OM Digital Solutions sp. z o.o. | PL | pl | NDA, Umowa o pracę, Umowa B2B |
| OMD Systems sp. z o.o. | PL | pl | NDA, Consulting Agreement |
| OM Poland sp. z o.o. | PL | pl | NDA, Consulting Agreement |
| OMD Systems Ltd | UK | none | NDA, Consulting Agreement |
| OMD Systems Ukraine | UA | uk | NDA, Договір підряду |

## Фазы реализации

### Phase 1: CompanyTheme + параметризация PDF ✅
- `lib/theme.py` — CompanyTheme, SectionData, TemplateData dataclasses
- `lib/pdf_generators.py` — параметризация через TemplateData
- `BilingualRenderer` — EN + local language rendering
- 55/55 CLI тестов сохранены

### Phase 2: Odoo-модели шаблонов ✅
- `models/contract_template.py` — ws.contract.template
- `models/contract_template_section.py` — ws.contract.template.section
- `models/contract_document.py` — ws.contract.document
- Views: tree + form для шаблонов и документов
- Security: 7 access rules (user/manager)
- Меню: WS Contracts → Configuration → Contract Templates

### Phase 3: Seed Data ✅
- `data/nda_template_ws.xml` — 12 NDA секций Woodenshark
- `data/contract_template_ws.xml` — 23 Contract секции Woodenshark

### Phase 4: Генерация документов через wizard ✅
- Wizard с template selection (фильтр по компании)
- Legacy mode (без шаблона) для обратной совместимости
- Автосоздание ws.contract.document записи

### Phase 5: Odoo Sign интеграция ✅
- `action_send_for_signature()` — sign.template + sign.request
- Dual-signer: company signatory + employee
- Cron: hourly sign status check
- `action_mark_signed()` — manual fallback

### Phase 6: Финализация ✅
- `__manifest__.py` v18.0.2.0.0
- 55/55 тестов, обратная совместимость
- Commit `524861b`, pushed to GitHub

## Ключевые файлы

**Новые:**
- `lib/theme.py` — CompanyTheme, SectionData, TemplateData, BilingualRenderer palettes
- `models/contract_template.py` — ws.contract.template
- `models/contract_template_section.py` — ws.contract.template.section
- `models/contract_document.py` — ws.contract.document + Odoo Sign
- `views/contract_template_views.xml` — UI шаблонов + меню
- `views/contract_document_views.xml` — UI документов
- `data/nda_template_ws.xml` — seed NDA Woodenshark
- `data/contract_template_ws.xml` — seed Contract Woodenshark
- `data/cron.xml` — sign status cron

**Модифицированные:**
- `lib/pdf_generators.py` — параметризация, BilingualRenderer
- `models/hr_employee.py` — ws_document_ids, smart button
- `wizards/generate_wizard.py` — template selection
- `views/hr_employee_views.xml` — Documents tab + smart button
- `views/generate_wizard_views.xml` — template toggle
- `security/ir.model.access.csv` — 7 rules
- `__manifest__.py` — v2.0.0

## Инфраструктура

- **Test Odoo:** `https://omds-sh-test50-29526801.dev.odoo.com`
- **Production:** `omds-sh.odoo.com`
- **GitHub:** `perss-spec/ws-contracts`
- **Repo:** `/mnt/d/NAS-DATA/ws-contracts/`
