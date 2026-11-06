"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/zip_code/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ZipCodeClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.zippopotam.us"

    def get_by_zipcode(self, country: str, postal_code: str) -> dict[str, Any]:
        endpoint = f"{self.base_url}/{country}/{postal_code}"
        response = self._http.get(endpoint)
        response.raise_for_status()
        return response.json()

    def get_by_city(self, country: str, state: str, city: str) -> dict[str, Any]:
        endpoint = f"{self.base_url}/{country}/{state}/{city}"
        response = self._http.get(endpoint)
        response.raise_for_status()
        return response.json()
