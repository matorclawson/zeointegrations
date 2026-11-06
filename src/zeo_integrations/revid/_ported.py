"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/revid/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class RevidAIClient:
    def __init__(self, transport):
        self._http = transport
        base_url = "https://www.revid.ai/api/public/v2"
        headers = {"Content-Type": "application/json"}
        self.base_url = base_url
        self.headers = headers

    def _make_request(self, endpoint: str, data: dict[str, Any] = None):
        url = f"{self.base_url}/{endpoint}"
        response = self._http.post(url, headers=self.headers, json=data)
        return response

    def create_video(self, creation_params: dict[str, Any]):
        return self._make_request("render", creation_params)

    def get_status(self, project_id: str):
        return self._http.get(
            f"{self.base_url}/status", params={"pid": project_id}, headers=self.headers
        )

    def get_projects(self, limit: int = 10):
        return self._http.get(
            f"{self.base_url}/projects", params={"limit": limit}, headers=self.headers
        )

    def add_to_queue(self, queue_params: dict[str, Any]):
        return self._make_request("add-to-queue", queue_params)

    def publish_now(self, publish_params: dict[str, Any]):
        return self._make_request("publish-now", publish_params)
