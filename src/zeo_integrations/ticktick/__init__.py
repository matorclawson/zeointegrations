"""Bounded ticktick operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TickTickClient


class Client(BaseClient):
    provider = "ticktick"
    implementation = TickTickClient
    origins = ("https://api.ticktick.com",)
    operations = (
        "get_task",
        "create_task",
        "update_task",
        "complete_task",
        "delete_task",
        "get_projects",
        "get_project",
        "create_project",
        "update_project",
        "delete_project",
        "get_project_data",
    )
