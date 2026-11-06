"""Bounded linear operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import LinearClient


class Client(BaseClient):
    provider = "linear"
    implementation = LinearClient
    origins = ("https://api.linear.app",)
    operations = (
        "execute_query",
        "list_issues",
        "search_issues",
        "filter_issues",
        "create_issue",
        "update_issue",
        "create_comment",
        "list_projects",
        "get_project",
        "list_users",
        "list_teams",
        "get_team",
        "list_workflow_states",
        "list_labels",
    )
