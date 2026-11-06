"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/readwise/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ReadwiseClient:
    BASE_URL = "https://readwise.io/api/v3"
    AUTH_URL = "https://readwise.io/api/v2/auth/"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def save_document(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/save/", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def list_documents(self, params: dict[str, Any] = None) -> dict[str, Any]:
        """List documents with optional filtering"""
        response = self._http.get(
            f"{self.BASE_URL}/list/", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def update_document(
        self, document_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a document"""
        response = self._http.patch(
            f"{self.BASE_URL}/update/{document_id}/", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def delete_document(self, document_id: str) -> None:
        """Delete a document"""
        response = self._http.delete(
            f"{self.BASE_URL}/delete/{document_id}/", headers=self.headers
        )
        response.raise_for_status()
        return None
