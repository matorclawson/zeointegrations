"""Bounded browser_use operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import BrowserUseClient


class Client(BaseClient):
    provider = "browser_use"
    implementation = BrowserUseClient
    origins = ("https://api.browser-use.com",)
    operations = (
        "run_task",
        "stop_task",
        "pause_task",
        "resume_task",
        "get_task",
        "get_task_status",
        "get_task_media",
        "list_tasks",
        "check_balance",
        "me",
        "ping",
    )
