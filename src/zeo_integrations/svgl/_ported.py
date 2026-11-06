"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/svgl/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class SvglClient:
    BASE_URL = "https://api.svgl.app"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Accept": "application/json"}

    def get_all_svgs(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get all SVGs with optional limit"""
        params = {}
        if limit is not None:
            params["limit"] = limit
        response = self._http.get(self.BASE_URL, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_svg_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get SVGs filtered by category"""
        response = self._http.get(
            f"{self.BASE_URL}/category/{category}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_categories(self) -> list[dict[str, Any]]:
        """Get all available categories with counts"""
        response = self._http.get(f"{self.BASE_URL}/categories", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def search_svgs(self, query: str) -> list[dict[str, Any]]:
        """Search SVGs by name"""
        params = {"search": query}
        response = self._http.get(self.BASE_URL, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
