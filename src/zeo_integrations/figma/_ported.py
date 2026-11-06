"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/figma/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class FigmaClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"Content-Type": "application/json"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] = None,
        data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        response = self._http.request(
            method=method, url=url, headers=self.headers, params=params, json=data
        )
        response.raise_for_status()
        return response.json()

    def get_file(self, file_key: str) -> dict[str, Any]:
        return self._make_request("GET", f"files/{file_key}")

    def get_file_nodes(self, file_key: str, node_ids: list[str]) -> dict[str, Any]:
        params = {"ids": ",".join(node_ids)}
        return self._make_request("GET", f"files/{file_key}/nodes", params=params)

    def get_image(
        self, file_key: str, node_ids: list[str], format: str = "png", scale: float = 1
    ) -> dict[str, Any]:
        params = {"ids": ",".join(node_ids), "format": format, "scale": scale}
        return self._make_request("GET", f"images/{file_key}", params=params)

    def get_file_components(self, file_key: str) -> dict[str, Any]:
        return self._make_request("GET", f"files/{file_key}/components")

    def get_component_sets(self, file_key: str) -> dict[str, Any]:
        return self._make_request("GET", f"files/{file_key}/component_sets")

    def get_styles(self, file_key: str) -> dict[str, Any]:
        return self._make_request("GET", f"files/{file_key}/styles")

    def get_me(self) -> dict[str, Any]:
        return self._make_request("GET", "me")

    def get_team_projects(self, team_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"teams/{team_id}/projects")

    def get_team_components(self, team_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"teams/{team_id}/components")

    def get_team_component_sets(self, team_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"teams/{team_id}/component_sets")

    def get_team_styles(self, team_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"teams/{team_id}/styles")

    def get_project_files(
        self, project_id: str, branch_name: str | None = None
    ) -> dict[str, Any]:
        params = {}
        if branch_name:
            params["branch_name"] = branch_name
        return self._make_request("GET", f"projects/{project_id}/files", params=params)
