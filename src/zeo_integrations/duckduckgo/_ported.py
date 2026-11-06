"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/duckduckgo/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class DuckDuckGoClient:
    BASE_URL = "https://api.duckduckgo.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"
            )
        }

    def search(self, query: str) -> dict[str, Any]:
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1,
            "t": "aci_client",
        }
        response = self._http.get(self.BASE_URL, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def fetch_content(self, url: str) -> dict[str, Any]:
        response = self._http.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return {"url": url, "html": response.text, "status_code": response.status_code}
