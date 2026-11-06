"""Bounded browserbase operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import BrowserBaseClient


class Client(BaseClient):
    provider = "browserbase"
    implementation = BrowserBaseClient
    origins = ("https://api.browserbase.com",)
    operations = (
        "get_session",
        "create_session",
        "update_session",
        "list_sessions",
        "get_context",
        "create_context",
        "delete_context",
        "get_session_logs",
        "get_session_recording",
        "get_session_debug",
        "get_session_downloads",
        "create_session_uploads",
        "list_projects",
        "get_project",
        "get_project_usage",
        "get_extension",
        "delete_extension",
    )
