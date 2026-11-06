"""Bounded motion operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import MotionClient


class Client(BaseClient):
    provider = "motion"
    implementation = MotionClient
    origins = ("https://api.usemotion.com",)
    operations = (
        "create_comment",
        "get_comments",
        "create_project",
        "get_project",
        "list_projects",
        "create_recurring_task",
        "delete_recurring_task",
        "list_recurring_tasks",
        "get_schedules",
        "get_statuses",
        "list_users",
        "get_my_user",
        "list_workspaces",
        "create_task",
        "delete_task",
        "get_task",
        "list_tasks",
        "move_task",
        "unassign_task",
        "update_task",
    )
