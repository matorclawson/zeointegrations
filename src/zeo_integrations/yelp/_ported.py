"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/yelp/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class YelpClient:
    BASE_URL = "https://yelp-business-api.p.rapidapi.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"x-rapidapi-host": "yelp-business-api.p.rapidapi.com"}

    def search_businesses(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Search for businesses based on location, search term, and other filters.
        """
        response = self._http.get(
            f"{self.BASE_URL}/search", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_business_details(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Get detailed information about one or more businesses.
        Can be queried by business_url or business_ids.
        """
        response = self._http.get(
            f"{self.BASE_URL}/each", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_business_reviews(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Get reviews for a specific business.
        Requires business_url or business_id and optional reviews_per_page parameter.
        """
        response = self._http.get(
            f"{self.BASE_URL}/reviews", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_business_menus(self, business_id: str) -> dict[str, Any]:
        """
        Get menu information for a specific business by ID.
        """
        params = {"business_id": business_id}
        response = self._http.get(
            f"{self.BASE_URL}/get_menus", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()
