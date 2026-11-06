"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/openweather/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class WeatherClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_weather_by_city(self, city: str, country: str) -> dict[str, Any]:
        params = {"q": f"{city},{country}", "units": "metric"}
        response = self._http.get(f"{self.base_url}/weather", params=params)
        response.raise_for_status()
        return response.json()

    def get_forecast_by_city(self, city: str, country: str) -> dict[str, Any]:
        params = {"q": f"{city},{country}", "units": "metric"}
        response = self._http.get(f"{self.base_url}/forecast", params=params)
        response.raise_for_status()
        return response.json()
