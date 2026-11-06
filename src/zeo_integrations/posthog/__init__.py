"""Bounded posthog operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import PosthogClient


class Client(BaseClient):
    provider = "posthog"
    implementation = PosthogClient
    origins = ("https://us.posthog.com",)
    operations = (
        "execute_query",
        "get_query",
        "delete_query",
        "get_insights",
        "create_insight",
        "get_insight",
        "update_insight",
        "check_auth",
        "get_dashboards",
        "create_dashboard",
        "get_dashboard",
        "update_dashboard",
        "get_events",
        "get_event",
        "get_projects",
        "get_project",
        "get_organizations",
        "get_organization",
        "get_organization_members",
        "get_persons",
        "get_person",
        "update_person",
        "delete_person",
        "bulk_delete_persons",
        "get_actions",
        "create_action",
        "get_action",
        "update_action",
        "delete_action",
        "get_feature_flags",
        "create_feature_flag",
        "get_feature_flag",
        "update_feature_flag",
        "delete_feature_flag",
    )
