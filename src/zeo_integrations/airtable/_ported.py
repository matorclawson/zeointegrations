"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/airtable/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class AirtableClient:
    BASE_URL = "https://api.airtable.com/v0"
    CONTENT_URL = "https://content.airtable.com/v0"
    META_URL = "https://api.airtable.com/v0/meta"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def list_records(
        self, base_id: str, table_id_or_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}"
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_record(
        self,
        base_id: str,
        table_id_or_name: str,
        record_id: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}/{record_id}"
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def create_records(
        self, base_id: str, table_id_or_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}"
        response = self._http.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_records(
        self,
        base_id: str,
        table_id_or_name: str,
        data: dict[str, Any],
        is_patch: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}"
        method = self._http.patch if is_patch else self._http.put
        response = method(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_record(
        self,
        base_id: str,
        table_id_or_name: str,
        record_id: str,
        data: dict[str, Any],
        is_patch: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}/{record_id}"
        method = self._http.patch if is_patch else self._http.put
        response = method(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete_records(
        self, base_id: str, table_id_or_name: str, record_ids: list[str]
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}"
        params = {"records[]": record_ids}
        response = self._http.delete(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def delete_record(
        self, base_id: str, table_id_or_name: str, record_id: str
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{base_id}/{table_id_or_name}/{record_id}"
        response = self._http.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def upload_attachment(
        self,
        base_id: str,
        record_id: str,
        attachment_field: str,
        file_data: dict[str, Any],
    ) -> dict[str, Any]:
        url = (
            f"{self.CONTENT_URL}/{base_id}/{record_id}/"
            f"{attachment_field}/uploadAttachment"
        )
        response = self._http.post(url, headers=self.headers, json=file_data)
        response.raise_for_status()
        return response.json()

    def sync_csv(
        self,
        base_id: str,
        table_id_or_name: str,
        api_endpoint_sync_id: str,
        csv_data: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.BASE_URL}/{base_id}/{table_id_or_name}/sync/{api_endpoint_sync_id}"
        )
        headers = {**self.headers, "Content-Type": "text/csv"}
        response = self._http.post(url, headers=headers, data=csv_data)
        response.raise_for_status()
        return response.json()

    def create_field(
        self, base_id: str, table_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.META_URL}/bases/{base_id}/tables/{table_id}/fields"
        response = self._http.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_field(
        self, base_id: str, table_id: str, column_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.META_URL}/bases/{base_id}/tables/{table_id}/fields/{column_id}"
        response = self._http.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_table(self, base_id: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.META_URL}/bases/{base_id}/tables"
        response = self._http.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_table(
        self, base_id: str, table_id_or_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.META_URL}/bases/{base_id}/tables/{table_id_or_name}"
        response = self._http.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def list_bases(self, offset: str | None = None) -> dict[str, Any]:
        url = f"{self.META_URL}/bases"
        params = {}
        if offset:
            params["offset"] = offset
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_base_schema(
        self, base_id: str, include: list[str] | None = None
    ) -> dict[str, Any]:
        url = f"{self.META_URL}/bases/{base_id}/tables"
        params = {}
        if include:
            params["include"] = include
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def create_base(self, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.META_URL}/bases"
        response = self._http.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def list_webhooks(self, base_id: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks"
        response = self._http.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_webhook(self, base_id: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks"
        response = self._http.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete_webhook(self, base_id: str, webhook_id: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}"
        response = self._http.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_webhook_payloads(
        self, base_id: str, webhook_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/bases/{base_id}/webhooks/{webhook_id}/payloads"
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_info(self) -> dict[str, Any]:
        url = f"{self.META_URL}/whoami"
        response = self._http.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
