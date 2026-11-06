"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/hunterio/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class HunterIOClient:
    BASE_URL = "https://api.hunter.io/v2"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Hunter.io API"""
        url = f"{self.BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        if method.upper() == "GET":
            response = self._http.get(url, params=params, headers=self.headers)
        elif method.upper() == "POST":
            response = self._http.post(
                url, params=params, json=data, headers=self.headers
            )
        elif method.upper() == "PUT":
            response = self._http.put(
                url, params=params, json=data, headers=self.headers
            )
        elif method.upper() == "DELETE":
            response = self._http.delete(url, params=params, headers=self.headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        response.raise_for_status()
        return response.json()

    def domain_search(
        self,
        domain: str | None = None,
        company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        type_filter: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        required_field: str | None = None,
    ) -> dict[str, Any]:
        """
        Search for email addresses from a domain name or company name
        """
        params = {}
        if domain:
            params["domain"] = domain
        if company:
            params["company"] = company
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if type_filter:
            params["type"] = type_filter
        if seniority:
            params["seniority"] = seniority
        if department:
            params["department"] = department
        if required_field:
            params["required_field"] = required_field
        return self._make_request("domain-search", params=params)

    def email_finder(
        self,
        domain: str | None = None,
        company: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        full_name: str | None = None,
        max_duration: int | None = None,
    ) -> dict[str, Any]:
        """
        Find the most likely email address from a domain name, first name and last name
        """
        params = {}
        if domain:
            params["domain"] = domain
        if company:
            params["company"] = company
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if full_name:
            params["full_name"] = full_name
        if max_duration:
            params["max_duration"] = max_duration
        return self._make_request("email-finder", params=params)

    def email_verifier(self, email: str) -> dict[str, Any]:
        """
        Verify the deliverability of an email address
        """
        params = {"email": email}
        return self._make_request("email-verifier", params=params)

    def email_count(
        self,
        domain: str | None = None,
        company: str | None = None,
        type_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Get the number of email addresses we have for a domain or company
        """
        params = {}
        if domain:
            params["domain"] = domain
        if company:
            params["company"] = company
        if type_filter:
            params["type"] = type_filter
        return self._make_request("email-count", params=params)

    def account_information(self) -> dict[str, Any]:
        """
        Get information about your Hunter account
        """
        return self._make_request("account")

    def email_enrichment(
        self, email: str, clearbit_format: bool = False
    ) -> dict[str, Any]:
        """
        Retrieve all the information associated with an email address
        """
        params = {"email": email}
        if clearbit_format:
            params["clearbit_format"] = "1"
        return self._make_request("people/find", params=params)

    def company_enrichment(
        self, domain: str, clearbit_format: bool = False
    ) -> dict[str, Any]:
        """
        Retrieve all the information associated with a domain name
        """
        params = {"domain": domain}
        if clearbit_format:
            params["clearbit_format"] = "1"
        return self._make_request("companies/find", params=params)

    def combined_enrichment(
        self, email: str, clearbit_format: bool = False
    ) -> dict[str, Any]:
        """
        Retrieve information for an email address and its domain.
        """
        params = {"email": email}
        if clearbit_format:
            params["clearbit_format"] = "1"
        return self._make_request("combined/find", params=params)
