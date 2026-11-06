"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/google_maps/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class GoogleMapsClient:
    BASE_URL = "https://maps.googleapis.com/maps/api"

    def __init__(self, transport):
        self._http = transport

    def geocode(self, address: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/geocode/json"
        params = {"address": address}
        return self._make_request(url, params)

    def reverse_geocode(self, latitude: float, longitude: float) -> dict[str, Any]:
        url = f"{self.BASE_URL}/geocode/json"
        params = {"latlng": f"{latitude},{longitude}"}
        return self._make_request(url, params)

    def search_places(
        self,
        query: str,
        location: tuple[float, float] | None = None,
        radius: int | None = None,
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/place/textsearch/json"
        params = {"query": query}
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        return self._make_request(url, params)

    def place_details(self, place_id: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/place/details/json"
        params = {"place_id": place_id}
        return self._make_request(url, params)

    def distance_matrix(
        self, origins: list[str], destinations: list[str], mode: str = "driving"
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/distancematrix/json"
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
        }
        return self._make_request(url, params)

    def elevation(self, locations: list[tuple[float, float]]) -> dict[str, Any]:
        url = f"{self.BASE_URL}/elevation/json"
        location_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        params = {"locations": location_str}
        return self._make_request(url, params)

    def directions(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/directions/json"
        params = {"origin": origin, "destination": destination, "mode": mode}
        return self._make_request(url, params)

    def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(url, params=params)
        response.raise_for_status()
        return response.json()
