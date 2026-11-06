"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/docusign/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from datetime import datetime, timedelta
from typing import Any

from zeo_integrations._http import compatibility as requests


class DocuSignClient:
    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a request to DocuSign API"""
        response = self._http.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    def get_user_info(self) -> dict[str, Any]:
        """Get user information to validate token"""
        url = "https://account.docusign.com/oauth/userinfo"
        response = self._make_request("GET", url)
        return response.json()

    def create_envelope(
        self, account_id: str, envelope_definition: dict[str, Any]
    ) -> dict[str, Any]:
        """Create and send an envelope"""
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes"
        response = self._make_request("POST", url, json=envelope_definition)
        return response.json()

    def get_envelope(self, account_id: str, envelope_id: str) -> dict[str, Any]:
        """Get envelope information"""
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes/{envelope_id}"
        response = self._make_request("GET", url)
        return response.json()

    def get_document(
        self, account_id: str, envelope_id: str, document_id: str
    ) -> bytes:
        """Download a document from an envelope"""
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes/{envelope_id}/documents/{document_id}"
        response = self._make_request("GET", url)
        return response.content

    def create_recipient_view(
        self, account_id: str, envelope_id: str, view_request: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a recipient view (embedded signing)"""
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes/{envelope_id}/views/recipient"
        response = self._make_request("POST", url, json=view_request)
        return response.json()

    def get_form_data(self, account_id: str, envelope_id: str) -> dict[str, Any]:
        """Get form data from an envelope"""
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes/{envelope_id}/form_data"
        response = self._make_request("GET", url)
        return response.json()

    def get_envelopes(
        self,
        account_id: str,
        from_date: str | None = None,
        status: str | None = None,
        folder_ids: list[str] | None = None,
        transaction_ids: list[str] | None = None,
        envelope_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        url = f"https://docusign.net/restapi/v2.1/accounts/{account_id}/envelopes"
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        params = self._clean_params(
            {
                "from_date": from_date,
                "status": status,
                "folder_ids": ",".join(folder_ids) if folder_ids else None,
                "transaction_ids": ",".join(transaction_ids)
                if transaction_ids
                else None,
                "envelope_ids": ",".join(envelope_ids) if envelope_ids else None,
            }
        )
        response = self._make_request("GET", url, params=params)
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Clean parameters before sending to API"""
        return {k: v for k, v in params.items() if v is not None}
