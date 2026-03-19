"""XML-RPC client for Odoo 18."""

from __future__ import annotations

import xmlrpc.client
from typing import Any

from .config import OdooSettings


class OdooClient:
    def __init__(self, settings: OdooSettings | None = None):
        self.settings = settings or OdooSettings()
        self._uid: int | None = None
        self._common: xmlrpc.client.ServerProxy | None = None
        self._models: xmlrpc.client.ServerProxy | None = None

    @property
    def uid(self) -> int:
        if self._uid is None:
            self.authenticate()
        return self._uid  # type: ignore[return-value]

    def authenticate(self) -> int:
        s = self.settings
        self._common = xmlrpc.client.ServerProxy(f"{s.odoo_url}/xmlrpc/2/common")
        self._uid = self._common.authenticate(s.odoo_db, s.odoo_user, s.odoo_password, {})
        if not self._uid:
            raise ConnectionError("Odoo authentication failed")
        self._models = xmlrpc.client.ServerProxy(f"{s.odoo_url}/xmlrpc/2/object")
        return self._uid

    def execute(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        s = self.settings
        if self._models is None:
            self.authenticate()
        return self._models.execute_kw(  # type: ignore[union-attr]
            s.odoo_db, self.uid, s.odoo_password,
            model, method, list(args), kwargs,
        )

    def search_read(self, model: str, domain: list, fields: list[str] | None = None, limit: int = 0) -> list[dict]:
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        return self.execute(model, "search_read", domain, **kwargs)

    def create(self, model: str, values: dict) -> int:
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        return self.execute(model, "write", ids, values)

    def get_employee(self, employee_id: int, fields: list[str] | None = None) -> dict:
        records = self.search_read("hr.employee", [["id", "=", employee_id]], fields=fields, limit=1)
        if not records:
            raise ValueError(f"Employee {employee_id} not found")
        return records[0]

    def get_all_employees(self, fields: list[str] | None = None) -> list[dict]:
        return self.search_read("hr.employee", [], fields=fields)
