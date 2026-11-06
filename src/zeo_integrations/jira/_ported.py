"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/jira/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class JiraClient:
    def __init__(self, transport, cloud_id: str):
        self._http = transport
        self.session = self._http
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        self.base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/2"
        self.cloud_id = cloud_id
        self.browser_base_url = None
        self.site_id = None

    def get_accessible_resources(self) -> list[dict[str, Any]]:
        response = self.session.get(
            "https://api.atlassian.com/oauth/token/accessible-resources", headers={}
        )
        response.raise_for_status()
        return response.json()

    def initialize_client(self):
        resources = self.get_accessible_resources()
        if not resources:
            raise Exception("No Jira resources available")
        resource = resources[0]
        self.cloud_id = resource["id"]
        self.site_id = (
            resource.get("url", "").split("/")[-1].replace(".atlassian.net", "")
        )
        self.base_url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/2"
        self.browser_base_url = f"https://{self.site_id}.atlassian.net"
        return resource

    def get_server_info(self) -> dict[str, Any]:
        if not self.cloud_id:
            self.initialize_client()
        response = self.session.get(
            f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/3/serverInfo",
            headers={},
        )
        response.raise_for_status()
        return response.json()

    def make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        if not self.base_url:
            self.initialize_client()
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        kwargs["headers"] = headers
        response = self.session.request(method, url, **kwargs)
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("errorMessages", [])
                if error_message:
                    error_message = error_message[0]
                else:
                    error_message = error_data.get("errors", {}).get(
                        "error", str(response.text)
                    )
                response.reason = error_message
            except Exception:
                pass
            response.raise_for_status()
        return response.json() if response.content else None

    def get_issue(self, issue_id: str) -> dict[str, Any]:
        return self.make_request("GET", f"issue/{issue_id}")

    def get_issue_comments(self, issue_id: str) -> dict[str, Any]:
        return self.make_request("GET", f"issue/{issue_id}/comment")

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        return self.make_request("POST", "issue", json={"fields": fields})

    def update_issue(self, issue_id: str, fields: dict[str, Any]) -> None:
        return self.make_request("PUT", f"issue/{issue_id}", json={"fields": fields})

    def delete_issue(self, issue_id: str) -> None:
        return self.make_request("DELETE", f"issue/{issue_id}")

    def transition_issue(self, issue_id: str, transition_id: str) -> dict[str, Any]:
        return self.make_request(
            "POST",
            f"issue/{issue_id}/transitions",
            json={"transition": {"id": transition_id}},
        )

    def search_issues(
        self, jql: str, start_at: int = 0, max_results: int = 50
    ) -> dict[str, Any]:
        params = {"jql": jql, "startAt": start_at, "maxResults": max_results}
        return self.make_request("GET", "search", params=params)

    def add_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        return self.make_request(
            "POST", f"issue/{issue_id}/comment", json={"body": body}
        )

    def get_comments(self, issue_id: str) -> list[dict[str, Any]]:
        response = self.make_request("GET", f"issue/{issue_id}/comment")
        return response.get("comments", [])

    def get_projects(self) -> list[dict[str, Any]]:
        """Get all accessible projects"""
        return self.make_request("GET", "project")

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Get detailed project information"""
        return self.make_request("GET", f"project/{project_id}")

    def get_all_statuses(self) -> list[dict[str, Any]]:
        """Get all available statuses"""
        return self.make_request("GET", "status")

    def get_all_priorities(self) -> list[dict[str, Any]]:
        """Get all available priorities"""
        return self.make_request("GET", "priority")

    def get_all_issue_types(self) -> list[dict[str, Any]]:
        """Get all issue types"""
        return self.make_request("GET", "issuetype")

    def get_all_fields(self) -> list[dict[str, Any]]:
        """Get all available fields"""
        return self.make_request("GET", "field")

    def get_users(self, query: str | None = None) -> list[dict[str, Any]]:
        """Get users that match the search query"""
        params = {"query": query if query else ""}
        return self.make_request("GET", "user/search", params=params)

    def get_transitions(self, issue_id: str) -> dict[str, Any]:
        return self.make_request("GET", f"issue/{issue_id}/transitions")
