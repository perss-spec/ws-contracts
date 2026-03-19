"""CLI interface: generate, generate-all, check, sync-fields."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .config import OdooSettings, PdfSettings
from .field_mapping import ODOO_FIELDS, map_employee
from .field_setup import sync_fields
from .models import EmployeeData
from .odoo_client import OdooClient
from .pdf.contract import ContractPdfGenerator
from .pdf.nda import NdaPdfGenerator
from .upload import upload_pdf


def _get_client() -> OdooClient:
    return OdooClient(OdooSettings())


def _get_pdf_settings() -> PdfSettings:
    return PdfSettings()


@click.group()
def main() -> None:
    """ws-contracts — NDA & Contract PDF generator for Odoo."""


@main.command()
@click.argument("employee_id", type=int)
@click.option("--type", "doc_type", type=click.Choice(["nda", "contract", "both"]), default="both")
@click.option("-o", "--output", "output_dir", type=click.Path(), default="./output")
@click.option("--upload/--no-upload", default=False, help="Upload PDF to Odoo")
@click.option("--dry-run", is_flag=True, help="Validate only, don't generate")
def generate(employee_id: int, doc_type: str, output_dir: str, upload: bool, dry_run: bool) -> None:
    """Generate NDA/Contract PDF for employee by Odoo ID."""
    client = _get_client()
    settings = _get_pdf_settings()

    record = client.get_employee(employee_id, fields=ODOO_FIELDS)
    emp = map_employee(record)

    # Validate
    if doc_type in ("nda", "both"):
        missing = emp.validate_for_nda()
        if missing:
            click.echo(f"NDA missing fields: {', '.join(missing)}", err=True)
            if not dry_run:
                sys.exit(1)

    if doc_type in ("contract", "both"):
        missing = emp.validate_for_contract()
        if missing:
            click.echo(f"Contract missing fields: {', '.join(missing)}", err=True)
            if not dry_run:
                sys.exit(1)

    if dry_run:
        click.echo(f"Employee {emp.full_name_lat}: validation passed")
        return

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if doc_type in ("nda", "both"):
        gen = NdaPdfGenerator(settings.fonts_dir)
        pdf_bytes = gen.generate(emp)
        fname = gen.get_filename(emp)
        (out / fname).write_bytes(pdf_bytes)
        click.echo(f"Generated: {out / fname} ({len(pdf_bytes):,} bytes)")
        if upload:
            att_id = upload_pdf(client, employee_id, fname, pdf_bytes)
            click.echo(f"Uploaded NDA → attachment id={att_id}")

    if doc_type in ("contract", "both"):
        gen_c = ContractPdfGenerator(settings.fonts_dir)
        pdf_bytes = gen_c.generate(emp)
        fname = gen_c.get_filename(emp)
        (out / fname).write_bytes(pdf_bytes)
        click.echo(f"Generated: {out / fname} ({len(pdf_bytes):,} bytes)")
        if upload:
            att_id = upload_pdf(client, employee_id, fname, pdf_bytes)
            click.echo(f"Uploaded Contract → attachment id={att_id}")


@main.command("generate-all")
@click.option("--type", "doc_type", type=click.Choice(["nda", "contract", "both"]), default="both")
@click.option("-o", "--output", "output_dir", type=click.Path(), default="./output")
@click.option("--upload/--no-upload", default=False)
def generate_all(doc_type: str, output_dir: str, upload: bool) -> None:
    """Generate PDFs for all employees."""
    client = _get_client()
    settings = _get_pdf_settings()
    records = client.get_all_employees(fields=ODOO_FIELDS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for record in records:
        emp = map_employee(record)
        eid = record["id"]

        if doc_type in ("nda", "both"):
            if not emp.validate_for_nda():
                gen = NdaPdfGenerator(settings.fonts_dir)
                pdf_bytes = gen.generate(emp)
                fname = gen.get_filename(emp)
                (out / fname).write_bytes(pdf_bytes)
                click.echo(f"[{eid}] {fname}")
                if upload:
                    upload_pdf(client, eid, fname, pdf_bytes)
            else:
                click.echo(f"[{eid}] NDA skipped — missing fields", err=True)

        if doc_type in ("contract", "both"):
            if not emp.validate_for_contract():
                gen_c = ContractPdfGenerator(settings.fonts_dir)
                pdf_bytes = gen_c.generate(emp)
                fname = gen_c.get_filename(emp)
                (out / fname).write_bytes(pdf_bytes)
                click.echo(f"[{eid}] {fname}")
                if upload:
                    upload_pdf(client, eid, fname, pdf_bytes)
            else:
                click.echo(f"[{eid}] Contract skipped — missing fields", err=True)


@main.command()
@click.argument("employee_id", type=int)
def check(employee_id: int) -> None:
    """Check employee data completeness for NDA/Contract."""
    client = _get_client()
    record = client.get_employee(employee_id, fields=ODOO_FIELDS)
    emp = map_employee(record)

    click.echo(f"Employee: {emp.full_name_lat} (id={employee_id})")

    nda_missing = emp.validate_for_nda()
    if nda_missing:
        click.echo(f"  NDA missing: {', '.join(nda_missing)}")
    else:
        click.echo("  NDA: OK")

    contract_missing = emp.validate_for_contract()
    if contract_missing:
        click.echo(f"  Contract missing: {', '.join(contract_missing)}")
    else:
        click.echo("  Contract: OK")


@main.command("sync-fields")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
def sync_fields_cmd(dry_run: bool) -> None:
    """Create missing x_ custom fields in hr.employee."""
    client = _get_client()
    created = sync_fields(client, dry_run=dry_run)
    if created:
        prefix = "[DRY RUN] Would create" if dry_run else "Created"
        for name in created:
            click.echo(f"  {prefix}: {name}")
    else:
        click.echo("All custom fields already exist.")


if __name__ == "__main__":
    main()
