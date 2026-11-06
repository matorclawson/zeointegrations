"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/twentyfirst_dev/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class TwentyFirstDevClient:
    BASE_URL = "https://21st.dev"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"content-type": "application/json"}

    def search(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/api/search", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()

    def generate_prompt(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/api/prompts", headers=self.headers, json=params
        )
        response.raise_for_status()
        return response.json()
