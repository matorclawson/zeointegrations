"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/tavily/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class TavilyClient:
    BASE_URL = "https://api.tavily.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def search(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a search query using Tavily Search API"""
        response = self._http.post(
            f"{self.BASE_URL}/search",
            headers=self.headers,
            json=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def extract(self, params: dict[str, Any]) -> dict[str, Any]:
        """Extract web page content from one or more URLs using Tavily Extract API"""
        response = self._http.post(
            f"{self.BASE_URL}/extract",
            headers=self.headers,
            json=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Clean and prepare parameters for API request"""
        cleaned = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                cleaned[k] = v
            elif isinstance(v, list):
                if k == "urls" and len(v) == 1:
                    cleaned[k] = v[0]
                else:
                    cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned
