"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/apollo/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ApolloClient:
    BASE_URL = "https://apollo-io-no-cookies-required.p.rapidapi.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {
            "x-rapidapi-host": "apollo-io-no-cookies-required.p.rapidapi.com",
            "Content-Type": "application/json",
        }

    def search_people(self, params: dict[str, Any]) -> dict[str, Any]:
        query_params = self._clean_params(params)
        response = self._http.get(
            f"{self.BASE_URL}/search_people", headers=self.headers, params=query_params
        )
        pass
        response.raise_for_status()
        return response.json()

    def search_people_by_url(self, params: dict[str, Any]) -> dict[str, Any]:
        data = self._clean_params(params)
        response = self._http.post(
            f"{self.BASE_URL}/search_people_via_url", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def search_organizations(self, params: dict[str, Any]) -> dict[str, Any]:
        query_params = self._clean_params(params)
        response = self._http.get(
            f"{self.BASE_URL}/search_organization",
            headers=self.headers,
            params=query_params,
        )
        response.raise_for_status()
        return response.json()

    def search_organizations_by_url(self, params: dict[str, Any]) -> dict[str, Any]:
        data = self._clean_params(params)
        response = self._http.post(
            f"{self.BASE_URL}/search_organizations_via_url",
            headers=self.headers,
            json=data,
        )
        response.raise_for_status()
        return response.json()

    def get_person_details(self, params: dict[str, Any]) -> dict[str, Any]:
        query_params = self._clean_params(params)
        response = self._http.get(
            f"{self.BASE_URL}/person_details", headers=self.headers, params=query_params
        )
        response.raise_for_status()
        return response.json()

    def get_organization_details(self, params: dict[str, Any]) -> dict[str, Any]:
        query_params = self._clean_params(params)
        response = self._http.get(
            f"{self.BASE_URL}/organization_details",
            headers=self.headers,
            params=query_params,
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for k, v in params.items():
            if v is None:
                continue
            cleaned[k] = v
        return cleaned
