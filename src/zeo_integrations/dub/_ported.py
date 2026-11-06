"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/dub/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class DubClient:
    BASE_URL = "https://api.dub.co"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def create_link(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/links", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def update_link(self, link_id: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/links/{link_id}", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def upsert_link(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/links/upsert", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def delete_link(self, link_id: str) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/links/{link_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_link_info(self, link_id: str = None) -> dict[str, Any]:
        url = f"{self.BASE_URL}/links/info"
        if link_id:
            url = f"{self.BASE_URL}/links/{link_id}"
        response = self._http.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_links(self) -> list[dict[str, Any]]:
        response = self._http.get(f"{self.BASE_URL}/links", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_links_count(self) -> dict[str, int]:
        response = self._http.get(f"{self.BASE_URL}/links/count", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def bulk_create_links(self, links: list[dict[str, Any]]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/links/bulk", headers=self.headers, json=links
        )
        response.raise_for_status()
        return response.json()

    def bulk_update_links(self, links: list[dict[str, Any]]) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/links/bulk", headers=self.headers, json=links
        )
        response.raise_for_status()
        return response.json()

    def bulk_delete_links(self, link_ids: list[str]) -> dict[str, int]:
        response = self._http.delete(
            f"{self.BASE_URL}/links/bulk?linkIds={','.join(link_ids)}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_qr_code(self, link_id: str = None) -> str:
        url = f"{self.BASE_URL}/qr"
        if link_id:
            url = f"{url}?linkId={link_id}"
        response = self._http.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_analytics(self) -> dict[str, Any]:
        response = self._http.get(f"{self.BASE_URL}/analytics", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_events(self) -> list[dict[str, Any]]:
        response = self._http.get(f"{self.BASE_URL}/events", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_customer(self, customer_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/customers/{customer_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_customers(self) -> list[dict[str, Any]]:
        response = self._http.get(f"{self.BASE_URL}/customers", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_customer(
        self, customer_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/customers/{customer_id}",
            headers=self.headers,
            json=params,
        )
        response.raise_for_status()
        return response.json()

    def delete_customer(self, customer_id: str) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/customers/{customer_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def track_lead(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/track/lead", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def track_sale(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/track/sale", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def create_tag(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/tags", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def get_tags(self) -> list[dict[str, Any]]:
        response = self._http.get(f"{self.BASE_URL}/tags", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_tag(self, tag_id: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/tags/{tag_id}", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def create_domain(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/domains", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def update_domain(self, slug: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/domains/{slug}", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def delete_domain(self, slug: str) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/domains/{slug}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_domains(self) -> list[dict[str, Any]]:
        response = self._http.get(f"{self.BASE_URL}/domains", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_workspace(self, id_or_slug: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/workspaces/{id_or_slug}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_workspace(
        self, id_or_slug: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/workspaces/{id_or_slug}",
            headers=self.headers,
            json=params,
        )
        response.raise_for_status()
        return response.json()
