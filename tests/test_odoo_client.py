"""Tests for odoo_client.py — with mocked XML-RPC."""

from unittest.mock import MagicMock, patch

import pytest

from ws_contracts.config import OdooSettings
from ws_contracts.odoo_client import OdooClient


class TestOdooClient:

    def test_authenticate(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_common.authenticate.return_value = 2
            mock_proxy.side_effect = [mock_common, MagicMock()]

            client = OdooClient(OdooSettings(odoo_user="test", odoo_password="test"))
            uid = client.authenticate()
            assert uid == 2

    def test_authenticate_failure(self):
        with patch("xmlrpc.client.ServerProxy") as mock_proxy:
            mock_common = MagicMock()
            mock_common.authenticate.return_value = False
            mock_proxy.return_value = mock_common

            client = OdooClient(OdooSettings(odoo_user="bad", odoo_password="bad"))
            with pytest.raises(ConnectionError, match="authentication failed"):
                client.authenticate()

    def test_get_employee(self, mock_odoo_client: OdooClient):
        record = mock_odoo_client.get_employee(42)
        assert record["id"] == 42
        assert record["x_full_name_lat"] == "Oleksandr Petrenko"

    def test_search_read(self, mock_odoo_client: OdooClient):
        records = mock_odoo_client.search_read("hr.employee", [])
        assert len(records) == 1
