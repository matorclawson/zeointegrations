"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/postman/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class PostmanClient:
    BASE_URL = "https://api.getpostman.com"

    def __init__(self, transport):
        self._http = transport
        self._initialize_client()

    def _initialize_client(self):
        self.headers = {"Content-Type": "application/json"}

    def get_collections(self, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/collections",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_collection(
        self, collection_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/collections/{collection_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def update_collection(
        self, collection_id: str, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/collections/{collection_id}",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def delete_collection(
        self, collection_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/collections/{collection_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def create_collection(
        self, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/collections",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_environments(self, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/environments",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_environment(
        self, environment_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/environments/{environment_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def create_environment(
        self, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/environments",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def update_environment(
        self, environment_id: str, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/environments/{environment_id}",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def delete_environment(
        self, environment_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/environments/{environment_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def fork_collection(
        self,
        collection_id: str,
        data: dict[str, Any] = None,
        params: dict[str, Any] = None,
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/collections/fork/{collection_id}",
            headers=self.headers,
            json=data or {},
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_workspaces(self, params: dict[str, Any] = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/workspaces",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def get_workspace(
        self, workspace_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/workspaces/{workspace_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def create_workspace(
        self, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/workspaces",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def update_workspace(
        self, workspace_id: str, data: dict[str, Any], params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.put(
            f"{self.BASE_URL}/workspaces/{workspace_id}",
            headers=self.headers,
            json=data,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def delete_workspace(
        self, workspace_id: str, params: dict[str, Any] = None
    ) -> dict[str, Any]:
        response = self._http.delete(
            f"{self.BASE_URL}/workspaces/{workspace_id}",
            headers=self.headers,
            params=self._clean_params(params or {}),
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                cleaned[k] = str(v).lower()
            elif isinstance(v, list):
                cleaned[k] = ",".join(map(str, v))
            else:
                cleaned[k] = v
        return cleaned
