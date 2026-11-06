"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/firecrawl/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class FirecrawlClient:
    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, transport):
        self._http = transport
        self.session = self._http
        self.session.headers.update({"Content-Type": "application/json"})

    def scrape(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/scrape", json=params)

    def batch_scrape(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/batch/scrape", json=params)

    def get_batch_status(self, batch_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/batch/scrape/{batch_id}")

    def get_batch_errors(self, batch_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/batch/scrape/{batch_id}/errors")

    def crawl(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/crawl", json=params)

    def get_crawl_status(self, crawl_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/crawl/{crawl_id}")

    def cancel_crawl(self, crawl_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/crawl/{crawl_id}")

    def get_crawl_errors(self, crawl_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/crawl/{crawl_id}/errors")

    def map_site(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/map", json=params)

    def extract(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/extract", json=params)

    def get_extract_status(self, extract_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/extract/{extract_id}")

    def search(self, **params) -> dict[str, Any]:
        return self._make_request("POST", "/search", json=params)

    def get_credit_usage(self) -> dict[str, Any]:
        return self._make_request("GET", "/team/credit-usage")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
