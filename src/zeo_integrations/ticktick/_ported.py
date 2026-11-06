"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/ticktick/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class TickTickClient:
    BASE_URL = "https://api.ticktick.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def get_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/open/v1/project/{project_id}/task/{task_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def create_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/open/v1/task",
            json=task_data,
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def update_task(self, task_id: str, task_data: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/open/v1/task/{task_id}",
            json=task_data,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def complete_task(self, project_id: str, task_id: str) -> None:
        response = self._http.post(
            f"{self.BASE_URL}/open/v1/project/{project_id}/task/{task_id}/complete",
            headers=self.headers,
        )
        response.raise_for_status()

    def delete_task(self, project_id: str, task_id: str) -> None:
        response = self._http.delete(
            f"{self.BASE_URL}/open/v1/project/{project_id}/task/{task_id}",
            headers=self.headers,
        )
        response.raise_for_status()

    def get_projects(self) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/open/v1/project", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_project(self, project_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/open/v1/project/{project_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def create_project(self, project_data: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/open/v1/project", json=project_data, headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_project(
        self, project_id: str, project_data: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/open/v1/project/{project_id}",
            json=project_data,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def delete_project(self, project_id: str) -> None:
        response = self._http.delete(
            f"{self.BASE_URL}/open/v1/project/{project_id}", headers=self.headers
        )
        response.raise_for_status()

    def get_project_data(self, project_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/open/v1/project/{project_id}/data", headers=self.headers
        )
        response.raise_for_status()
        return response.json()
