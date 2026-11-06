"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/resend/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ResendClient:
    BASE_URL = "https://api.resend.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def send_email(self, email_data: dict[str, Any]) -> dict[str, Any]:
        """Send a single email through Resend API."""
        response = self._http.post(
            f"{self.BASE_URL}/emails", headers=self.headers, json=email_data
        )
        response.raise_for_status()
        return response.json()

    def send_batch_emails(self, emails_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Send multiple emails in a single batch request."""
        response = self._http.post(
            f"{self.BASE_URL}/emails/batch", headers=self.headers, json=emails_data
        )
        response.raise_for_status()
        return response.json()

    def get_email(self, email_id: str) -> dict[str, Any]:
        """Retrieve details of a specific email."""
        response = self._http.get(
            f"{self.BASE_URL}/emails/{email_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_email(self, email_id: str, scheduled_at: str) -> dict[str, Any]:
        """Update a scheduled email."""
        response = self._http.patch(
            f"{self.BASE_URL}/emails/{email_id}",
            headers=self.headers,
            json={"scheduled_at": scheduled_at},
        )
        response.raise_for_status()
        return response.json()

    def cancel_email(self, email_id: str) -> dict[str, Any]:
        """Cancel a scheduled email."""
        response = self._http.post(
            f"{self.BASE_URL}/emails/{email_id}/cancel", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_domain(self, domain_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new domain."""
        response = self._http.post(
            f"{self.BASE_URL}/domains", headers=self.headers, json=domain_data
        )
        response.raise_for_status()
        return response.json()

    def get_domain(self, domain_id: str) -> dict[str, Any]:
        """Retrieve details of a specific domain."""
        response = self._http.get(
            f"{self.BASE_URL}/domains/{domain_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def verify_domain(self, domain_id: str) -> dict[str, Any]:
        """Verify a domain."""
        response = self._http.post(
            f"{self.BASE_URL}/domains/{domain_id}/verify", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_domain(
        self, domain_id: str, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a domain."""
        response = self._http.patch(
            f"{self.BASE_URL}/domains/{domain_id}",
            headers=self.headers,
            json=update_data,
        )
        response.raise_for_status()
        return response.json()

    def list_domains(self) -> dict[str, Any]:
        """List all domains."""
        response = self._http.get(f"{self.BASE_URL}/domains", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def delete_domain(self, domain_id: str) -> dict[str, Any]:
        """Delete a domain."""
        response = self._http.delete(
            f"{self.BASE_URL}/domains/{domain_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_broadcast(self, broadcast_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new broadcast."""
        response = self._http.post(
            f"{self.BASE_URL}/broadcasts", headers=self.headers, json=broadcast_data
        )
        response.raise_for_status()
        return response.json()

    def get_broadcast(self, broadcast_id: str) -> dict[str, Any]:
        """Retrieve details of a specific broadcast."""
        response = self._http.get(
            f"{self.BASE_URL}/broadcasts/{broadcast_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def send_broadcast(
        self, broadcast_id: str, send_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a broadcast."""
        response = self._http.post(
            f"{self.BASE_URL}/broadcasts/{broadcast_id}/send",
            headers=self.headers,
            json=send_data,
        )
        response.raise_for_status()
        return response.json()

    def delete_broadcast(self, broadcast_id: str) -> dict[str, Any]:
        """Delete a broadcast."""
        response = self._http.delete(
            f"{self.BASE_URL}/broadcasts/{broadcast_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_broadcasts(self) -> dict[str, Any]:
        """List all broadcasts."""
        response = self._http.get(f"{self.BASE_URL}/broadcasts", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_audience(self, audience_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new audience."""
        response = self._http.post(
            f"{self.BASE_URL}/audiences", headers=self.headers, json=audience_data
        )
        response.raise_for_status()
        return response.json()

    def get_audience(self, audience_id: str) -> dict[str, Any]:
        """Retrieve details of a specific audience."""
        response = self._http.get(
            f"{self.BASE_URL}/audiences/{audience_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def delete_audience(self, audience_id: str) -> dict[str, Any]:
        """Delete an audience."""
        response = self._http.delete(
            f"{self.BASE_URL}/audiences/{audience_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_audiences(self) -> dict[str, Any]:
        """List all audiences."""
        response = self._http.get(f"{self.BASE_URL}/audiences", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_contact(
        self, audience_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new contact in an audience."""
        response = self._http.post(
            f"{self.BASE_URL}/audiences/{audience_id}/contacts",
            headers=self.headers,
            json=contact_data,
        )
        response.raise_for_status()
        return response.json()

    def get_contact(self, audience_id: str, contact_id: str) -> dict[str, Any]:
        """Retrieve details of a specific contact."""
        response = self._http.get(
            f"{self.BASE_URL}/audiences/{audience_id}/contacts/{contact_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def update_contact(
        self, audience_id: str, contact_identifier: str, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a contact. Contact identifier can be ID or email."""
        response = self._http.patch(
            f"{self.BASE_URL}/audiences/{audience_id}/contacts/{contact_identifier}",
            headers=self.headers,
            json=update_data,
        )
        response.raise_for_status()
        return response.json()

    def delete_contact(
        self, audience_id: str, contact_identifier: str
    ) -> dict[str, Any]:
        """Delete a contact. Contact identifier can be ID or email."""
        response = self._http.delete(
            f"{self.BASE_URL}/audiences/{audience_id}/contacts/{contact_identifier}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_contacts(self, audience_id: str) -> dict[str, Any]:
        """List all contacts in an audience."""
        response = self._http.get(
            f"{self.BASE_URL}/audiences/{audience_id}/contacts", headers=self.headers
        )
        response.raise_for_status()
        return response.json()
