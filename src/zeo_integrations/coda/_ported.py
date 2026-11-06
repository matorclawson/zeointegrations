"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/coda/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class CodaClient:
    BASE_URL = "https://coda.io/apis/v1"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def list_docs(self, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_doc(self, doc_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_pages(self, doc_id: str, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/pages",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_page(self, doc_id: str, page_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/pages/{page_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_page(self, doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/docs/{doc_id}/pages", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def update_page(
        self, doc_id: str, page_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/docs/{doc_id}/pages/{page_id}",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def delete_page(self, doc_id: str, page_id: str) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/docs/{doc_id}/pages/{page_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def export_page(
        self, doc_id: str, page_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/docs/{doc_id}/pages/{page_id}/export",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def get_export_status(
        self, doc_id: str, page_id: str, request_id: str
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/pages/{page_id}/export/{request_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                cleaned[k] = str(v).lower()
            elif isinstance(v, list):
                cleaned[k] = ",".join(map(str, v))
            else:
                cleaned[k] = v
        return cleaned

    def list_tables(self, doc_id: str, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_table(self, doc_id: str, table_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_columns(
        self, doc_id: str, table_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/columns",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_column(self, doc_id: str, table_id: str, column_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/columns/{column_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_rows(
        self, doc_id: str, table_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_row(self, doc_id: str, table_id: str, row_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows/{row_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def create_rows(
        self, doc_id: str, table_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def update_row(
        self, doc_id: str, table_id: str, row_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows/{row_id}",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def delete_rows(
        self, doc_id: str, table_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def delete_row(self, doc_id: str, table_id: str, row_id: str) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows/{row_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def push_button(
        self, doc_id: str, table_id: str, row_id: str, column_id: str
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/docs/{doc_id}/tables/{table_id}/rows/{row_id}/buttons/{column_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_formulas(
        self, doc_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/formulas",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_formula(self, doc_id: str, formula_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/formulas/{formula_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_controls(
        self, doc_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/controls",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_control(self, doc_id: str, control_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/docs/{doc_id}/controls/{control_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_whoami(self) -> dict[str, Any]:
        response = self._http.get(f"{self.BASE_URL}/whoami", headers=self.headers)
        response.raise_for_status()
        return response.json()
