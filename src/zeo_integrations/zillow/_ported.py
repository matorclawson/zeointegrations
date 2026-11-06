"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/zillow/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class ZillowClient:
    BASE_URL = "https://zillow-com1.p.rapidapi.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"x-rapidapi-host": "zillow-com1.p.rapidapi.com"}

    def get_property(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/property",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def search_properties(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/propertyExtendedSearch",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_zestimate(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/zestimate",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_zestimate_history(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/zestimateHistory",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_price_and_tax_history(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/priceAndTaxHistory",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_property_comps(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/propertyComps",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_property_value_range(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/valueEstimate",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_similar_properties(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/similarProperty",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_similar_sales(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/similarSales",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_similar_rentals(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/similarForRent",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_market_location(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/marketLocation",
            headers=self.headers,
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_market_data(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/marketData",
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
            cleaned[k] = v
        return cleaned
