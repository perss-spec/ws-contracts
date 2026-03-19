"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ws_contracts.cli import main


class TestCli:

    @patch("ws_contracts.cli._get_client")
    @patch("ws_contracts.cli._get_pdf_settings")
    def test_generate_dry_run(self, mock_settings, mock_client_fn, mock_odoo_client, pdf_settings):
        mock_client_fn.return_value = mock_odoo_client
        mock_settings.return_value = pdf_settings

        runner = CliRunner()
        result = runner.invoke(main, ["generate", "42", "--dry-run"])
        assert result.exit_code == 0
        assert "validation passed" in result.output

    @patch("ws_contracts.cli._get_client")
    def test_check(self, mock_client_fn, mock_odoo_client):
        mock_client_fn.return_value = mock_odoo_client

        runner = CliRunner()
        result = runner.invoke(main, ["check", "42"])
        assert result.exit_code == 0
        assert "Oleksandr Petrenko" in result.output
        assert "NDA: OK" in result.output

    @patch("ws_contracts.cli._get_client")
    def test_sync_fields_dry_run(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client.search_read.side_effect = [
            [{"id": 1}],  # ir.model lookup
            [],            # no existing fields
        ]
        mock_client_fn.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(main, ["sync-fields", "--dry-run"])
        assert result.exit_code == 0
        assert "x_full_name_lat" in result.output
