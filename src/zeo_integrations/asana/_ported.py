"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/asana/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class AsanaClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://app.asana.com/api/1.0"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

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

    def get_tasks(
        self,
        workspace_id: str,
        project_id: str | None = None,
        assignee: str | None = None,
        completed_since: str | None = None,
        limit: int = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            "opt_fields": (
                "gid,name,completed,due_on,notes,assignee,assignee.gid,assign"
                "ee.name,assignee.email,workspace,workspace.gid,workspace.nam"
                "e,projects,projects.gid,projects.name,parent,parent.gid,pare"
                "nt.name,created_at,modified_at"
            ),
        }
        if project_id:
            params["project"] = project_id
        if workspace_id and (not project_id):
            params["workspace"] = workspace_id
        if assignee:
            params["assignee"] = assignee
        if completed_since:
            params["completed_since"] = completed_since
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "tasks", params=params)

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"tasks/{task_id}")

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("POST", "tasks", data={"data": data})

    def update_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("PUT", f"tasks/{task_id}", data={"data": data})

    def delete_task(self, task_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"tasks/{task_id}")

    def get_subtasks(self, task_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"tasks/{task_id}/subtasks")

    def create_subtask(
        self, parent_task_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        data["parent"] = parent_task_id
        return self._make_request("POST", "tasks", data={"data": data})

    def get_workspaces(
        self, limit: int = 20, offset: str | None = None
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "workspaces", params=params)

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"workspaces/{workspace_id}")

    def get_projects(
        self,
        workspace_id: str | None = None,
        team_id: str | None = None,
        archived: bool | None = None,
        limit: int = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if workspace_id:
            params["workspace"] = workspace_id
        if team_id:
            params["team"] = team_id
        if archived is not None:
            params["archived"] = str(archived).lower()
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "projects", params=params)

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"projects/{project_id}")

    def get_goals(
        self,
        workspace_id: str,
        time_period_id: str | None = None,
        owner_id: str | None = None,
        is_workspace_level: bool | None = None,
        limit: int = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if workspace_id:
            params["workspace"] = workspace_id
        if time_period_id:
            params["time_period"] = time_period_id
        if owner_id:
            params["owner"] = owner_id
        if is_workspace_level is not None:
            params["is_workspace_level"] = str(is_workspace_level).lower()
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "goals", params=params)

    def get_goal(self, goal_id: str) -> dict[str, Any]:
        params = {
            "opt_fields": (
                "gid,name,due_on,notes,status,owner,owner.gid,owner.name,owne"
                "r.email,workspace,workspace.gid,workspace.name,time_period,t"
                "ime_period.gid,time_period.name,metric,metric.gid,metric.nam"
                "e,metric.precision,metric.unit,metric.current_number_value,m"
                "etric.target_number_value,is_workspace_level,liked"
            )
        }
        return self._make_request("GET", f"goals/{goal_id}", params=params)

    def create_goal(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("POST", "goals", data={"data": data})

    def update_goal(self, goal_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("PUT", f"goals/{goal_id}", data={"data": data})

    def get_tags(
        self,
        workspace_id: str | None = None,
        project_id: str | None = None,
        limit: int = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if workspace_id:
            params["workspace"] = workspace_id
        if project_id:
            params["project"] = project_id
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "tags", params=params)

    def get_tag(self, tag_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"tags/{tag_id}")

    def get_teams(
        self, workspace_id: str, limit: int = 20, offset: str | None = None
    ) -> dict[str, Any]:
        params = {"workspace": workspace_id, "limit": limit}
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "teams", params=params)

    def get_team(self, team_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"teams/{team_id}")

    def get_users(
        self,
        workspace_id: str | None = None,
        team_id: str | None = None,
        limit: int = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if workspace_id:
            params["workspace"] = workspace_id
        if team_id:
            params["team"] = team_id
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "users", params=params)

    def get_user(self, user_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"users/{user_id}")

    def get_sections(self, project_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"projects/{project_id}/sections")

    def get_section(self, section_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"sections/{section_id}")

    def get_section_tasks(
        self, section_id: str, limit: int = 20, offset: str | None = None
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            "opt_fields": (
                "gid,name,completed,due_on,notes,assignee,assignee.gid,assign"
                "ee.name,assignee.email,workspace,workspace.gid,workspace.nam"
                "e,projects,projects.gid,projects.name,parent,parent.gid,pare"
                "nt.name,created_at,modified_at"
            ),
        }
        if offset:
            params["offset"] = offset
        return self._make_request("GET", f"sections/{section_id}/tasks", params=params)

    def get_time_periods(
        self, workspace_id: str, limit: int = 20, offset: str | None = None
    ) -> dict[str, Any]:
        params = {
            "workspace": workspace_id,
            "limit": limit,
            "opt_fields": "gid,name,start_on,end_on,period,workspace,parent",
        }
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "time_periods", params=params)

    def get_goal_time_periods(
        self, workspace_id: str, limit: int = 20, offset: str | None = None
    ) -> dict[str, Any]:
        params = {
            "workspace": workspace_id,
            "limit": limit,
            "opt_fields": "gid,name,start_on,end_on,period,workspace,parent",
        }
        if offset:
            params["offset"] = offset
        return self._make_request("GET", "goals/time_periods", params=params)
