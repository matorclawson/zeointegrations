"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/motion/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class MotionClient:
    BASE_URL = "https://api.usemotion.com/v1"

    def __init__(self, transport):
        self._http = transport
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_comment(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new comment on a task"""
        response = self._http.post(
            f"{self.BASE_URL}/comments", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def get_comments(self, task_id: str, cursor: str | None = None) -> dict[str, Any]:
        """Get all comments for a task"""
        params = {"taskId": task_id}
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(
            f"{self.BASE_URL}/comments", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new project"""
        response = self._http.post(
            f"{self.BASE_URL}/projects", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Get a single project by ID"""
        response = self._http.get(
            f"{self.BASE_URL}/projects/{project_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_projects(
        self, workspace_id: str | None = None, cursor: str | None = None
    ) -> dict[str, Any]:
        """List all projects for a workspace"""
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(
            f"{self.BASE_URL}/projects", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def create_recurring_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new recurring task"""
        response = self._http.post(
            f"{self.BASE_URL}/recurring-tasks", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_recurring_task(self, task_id: str) -> dict[str, Any]:
        """Delete a recurring task by ID"""
        response = self._http.delete(
            f"{self.BASE_URL}/recurring-tasks/{task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json() if response.content else {"success": True}

    def list_recurring_tasks(
        self, workspace_id: str, cursor: str | None = None
    ) -> dict[str, Any]:
        """List all recurring tasks for a workspace"""
        params = {"workspaceId": workspace_id}
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(
            f"{self.BASE_URL}/recurring-tasks", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_schedules(self) -> list[dict[str, Any]]:
        """Get all schedules for the authenticated user"""
        response = self._http.get(f"{self.BASE_URL}/schedules", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_statuses(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        """Get a list of statuses for a workspace"""
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        response = self._http.get(
            f"{self.BASE_URL}/statuses", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def list_users(
        self,
        team_id: str | None = None,
        workspace_id: str | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Get a list of users for a team or workspace"""
        params = {}
        if team_id:
            params["teamId"] = team_id
        if workspace_id:
            params["workspaceId"] = workspace_id
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(
            f"{self.BASE_URL}/users", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_my_user(self) -> dict[str, Any]:
        """Get information about the authenticated user"""
        response = self._http.get(f"{self.BASE_URL}/users/me", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_workspaces(
        self, ids: list[str] | None = None, cursor: str | None = None
    ) -> dict[str, Any]:
        """Get a list of workspaces the user is part of"""
        params = {}
        if ids:
            params["ids"] = ",".join(ids)
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(
            f"{self.BASE_URL}/workspaces", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new task"""
        response = self._http.post(
            f"{self.BASE_URL}/tasks", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_task(self, task_id: str) -> dict[str, Any]:
        """Delete a task by ID"""
        response = self._http.delete(
            f"{self.BASE_URL}/tasks/{task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json() if response.content else {"success": True}

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Get a task by ID"""
        response = self._http.get(
            f"{self.BASE_URL}/tasks/{task_id}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def list_tasks(
        self,
        assignee_id: str | None = None,
        cursor: str | None = None,
        include_all_statuses: bool | None = None,
        label: str | None = None,
        name: str | None = None,
        project_id: str | None = None,
        status: list[str] | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        """List tasks based on query parameters"""
        params = {}
        if assignee_id:
            params["assigneeId"] = assignee_id
        if cursor:
            params["cursor"] = cursor
        if include_all_statuses is not None:
            params["includeAllStatuses"] = str(include_all_statuses).lower()
        if label:
            params["label"] = label
        if name:
            params["name"] = name
        if project_id:
            params["projectId"] = project_id
        if status:
            params["status"] = status
        if workspace_id:
            params["workspaceId"] = workspace_id
        response = self._http.get(
            f"{self.BASE_URL}/tasks", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def move_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Move a task to a different workspace"""
        response = self._http.patch(
            f"{self.BASE_URL}/tasks/{task_id}/move", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def unassign_task(self, task_id: str) -> dict[str, Any]:
        """Remove the assignee of a task"""
        response = self._http.delete(
            f"{self.BASE_URL}/tasks/{task_id}/assignee", headers=self.headers
        )
        response.raise_for_status()
        return response.json() if response.content else {"success": True}

    def update_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a task"""
        response = self._http.patch(
            f"{self.BASE_URL}/tasks/{task_id}", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()
