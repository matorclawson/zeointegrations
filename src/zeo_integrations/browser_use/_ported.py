"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/browser_use/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class BrowserUseClient:
    BASE_URL = "https://api.browser-use.com/api/v1"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def run_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/run-task", headers=self.headers, json=task_data
        )
        response.raise_for_status()
        return response.json()

    def stop_task(self, task_id: str) -> Any:
        response = self._http.put(
            f"{self.BASE_URL}/stop-task?task_id={task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def pause_task(self, task_id: str) -> Any:
        response = self._http.put(
            f"{self.BASE_URL}/pause-task?task_id={task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def resume_task(self, task_id: str) -> Any:
        response = self._http.put(
            f"{self.BASE_URL}/resume-task?task_id={task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_task(self, task_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/task/{task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_task_status(self, task_id: str) -> str:
        response = self._http.get(
            f"{self.BASE_URL}/task/{task_id}/status", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_task_media(self, task_id: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/task/{task_id}/media", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_tasks(self) -> dict[str, Any]:
        response = self._http.get(f"{self.BASE_URL}/tasks", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def check_balance(self) -> dict[str, int]:
        response = self._http.get(f"{self.BASE_URL}/balance", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def me(self) -> bool:
        response = self._http.get(f"{self.BASE_URL}/me", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def ping(self) -> Any:
        response = self._http.get(f"{self.BASE_URL}/ping")
        response.raise_for_status()
        return response.json()
