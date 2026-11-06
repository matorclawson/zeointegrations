"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/sentry/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any

from zeo_integrations._http import compatibility as requests


class SentryClient:
    BASE_URL = "https://sentry.io/api/0"

    def __init__(self, transport, org_slug: str):
        self._http = transport
        self.org_slug = org_slug
        self.headers = {"Content-Type": "application/json"}

    def _handle_response(self, response: requests.Response) -> dict:
        response.raise_for_status()
        return response.json()

    def list_organizations(self) -> dict:
        return self._handle_response(
            self._http.get(f"{self.BASE_URL}/organizations/", headers=self.headers)
        )

    def list_teams(self) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/organizations/{self.org_slug}/teams/",
                headers=self.headers,
            )
        )

    def create_team(self, data: dict[str, Any]) -> dict:
        return self._handle_response(
            self._http.post(
                f"{self.BASE_URL}/organizations/{self.org_slug}/teams/",
                headers=self.headers,
                json=data,
            )
        )

    def list_user_teams(self) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/organizations/{self.org_slug}/user-teams/",
                headers=self.headers,
            )
        )

    def list_projects(self) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/organizations/{self.org_slug}/projects/",
                headers=self.headers,
            )
        )

    def create_project(self, team_slug: str, data: dict[str, Any]) -> dict:
        return self._handle_response(
            self._http.post(
                f"{self.BASE_URL}/teams/{self.org_slug}/{team_slug}/projects/",
                headers=self.headers,
                json=data,
            )
        )

    def list_issues(
        self, project_slug: str, query_params: dict[str, Any] | None = None
    ) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/issues/",
                headers=self.headers,
                params=query_params,
            )
        )

    def get_issue_details(self, issue_id: str) -> dict:
        return self._handle_response(
            self._http.get(f"{self.BASE_URL}/issues/{issue_id}/", headers=self.headers)
        )

    def list_issue_events(
        self, issue_id: str, query_params: dict[str, Any] | None = None
    ) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/issues/{issue_id}/events/",
                headers=self.headers,
                params=query_params,
            )
        )

    def list_releases(self, query_params: dict[str, Any] | None = None) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/organizations/{self.org_slug}/releases/",
                headers=self.headers,
                params=query_params,
            )
        )

    def create_release(self, data: dict[str, Any]) -> dict:
        return self._handle_response(
            self._http.post(
                f"{self.BASE_URL}/organizations/{self.org_slug}/releases/",
                headers=self.headers,
                json=data,
            )
        )

    def list_alert_rules(self, project_slug: str) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/rules/",
                headers=self.headers,
            )
        )

    def create_alert_rule(self, project_slug: str, data: dict[str, Any]) -> dict:
        return self._handle_response(
            self._http.post(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/rules/",
                headers=self.headers,
                json=data,
            )
        )

    def list_user_feedback(
        self, project_slug: str, query_params: dict[str, Any] | None = None
    ) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/user-feedback/",
                headers=self.headers,
                params=query_params,
            )
        )

    def list_service_hooks(self, project_slug: str) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/hooks/",
                headers=self.headers,
            )
        )

    def create_service_hook(self, project_slug: str, data: dict[str, Any]) -> dict:
        return self._handle_response(
            self._http.post(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/hooks/",
                headers=self.headers,
                json=data,
            )
        )

    def get_project_dsn(self, project_slug: str) -> dict:
        return self._handle_response(
            self._http.get(
                f"{self.BASE_URL}/projects/{self.org_slug}/{project_slug}/keys/",
                headers=self.headers,
            )
        )
