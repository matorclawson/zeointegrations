"""Bounded sentry operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import SentryClient


class Client(BaseClient):
    provider = "sentry"
    implementation = SentryClient
    origins = ("https://sentry.io",)
    operations = (
        "list_organizations",
        "list_teams",
        "create_team",
        "list_user_teams",
        "list_projects",
        "create_project",
        "list_issues",
        "get_issue_details",
        "list_issue_events",
        "list_releases",
        "create_release",
        "list_alert_rules",
        "create_alert_rule",
        "list_user_feedback",
        "list_service_hooks",
        "create_service_hook",
        "get_project_dsn",
    )
