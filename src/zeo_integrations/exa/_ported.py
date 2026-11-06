"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/exa/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ExaClient:
    BASE_URL = "https://api.exa.ai"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"content-type": "application/json"}

    def search(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a search query"""
        response = self._http.post(
            f"{self.BASE_URL}/search",
            headers=self.headers,
            json=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_contents(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/contents", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def find_similar(self, params: dict[str, Any]) -> dict[str, Any]:
        """Find similar content to a given URL"""
        response = self._http.post(
            f"{self.BASE_URL}/findSimilar",
            headers=self.headers,
            json=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Clean parameters before sending to API"""
        cleaned = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                cleaned[k] = v
            elif isinstance(v, list):
                cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned
