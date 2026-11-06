"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/brave/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class BraveClient:
    BASE_URL = "https://api.search.brave.com/res/v1"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Accept": "application/json", "Accept-Encoding": "gzip"}

    def web_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform a web search"""
        response = self._http.get(
            f"{self.BASE_URL}/web/search",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def image_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """Perform an image search"""
        response = self._http.get(
            f"{self.BASE_URL}/images/search",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def video_search(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/videos/search",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def news_search(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/news/search",
            headers=self.headers,
            params=self._clean_params(params),
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
