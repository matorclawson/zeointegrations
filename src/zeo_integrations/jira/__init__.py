"""Bounded jira operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import JiraClient


class Client(BaseClient):
    provider = "jira"
    implementation = JiraClient
    origins = ("https://api.atlassian.com",)
    operations = (
        "get_accessible_resources",
        "get_server_info",
        "get_issue",
        "get_issue_comments",
        "create_issue",
        "update_issue",
        "delete_issue",
        "transition_issue",
        "search_issues",
        "add_comment",
        "get_comments",
        "get_projects",
        "get_project",
        "get_all_statuses",
        "get_all_priorities",
        "get_all_issue_types",
        "get_all_fields",
        "get_users",
        "get_transitions",
    )
