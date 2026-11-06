"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/perplexity/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class PerplexityClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.perplexity.ai/chat/completions"

    def create_completion(self, **kwargs) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        response = self._http.post(self.base_url, json=kwargs, headers=headers)
        response.raise_for_status()
        return response.json()
