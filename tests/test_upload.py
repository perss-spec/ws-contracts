"""Tests for upload.py."""

from unittest.mock import MagicMock

from ws_contracts.upload import upload_pdf


class TestUpload:

    def test_upload_attachment(self, mock_odoo_client: MagicMock):
        mock_odoo_client.create.return_value = 999
        att_id = upload_pdf(mock_odoo_client, 42, "NDA Test.pdf", b"%PDF-1.7 test")
        assert att_id == 999
        mock_odoo_client.create.assert_called_once()
        call_args = mock_odoo_client.create.call_args
        assert call_args[0][0] == "ir.attachment"
        vals = call_args[0][1]
        assert vals["name"] == "NDA Test.pdf"
        assert vals["res_model"] == "hr.employee"
        assert vals["res_id"] == 42
