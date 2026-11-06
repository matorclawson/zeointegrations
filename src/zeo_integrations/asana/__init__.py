"""Bounded asana operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import AsanaClient


class Client(BaseClient):
    provider = "asana"
    implementation = AsanaClient
    origins = ("https://app.asana.com",)
    operations = (
        "get_tasks",
        "get_task",
        "create_task",
        "update_task",
        "delete_task",
        "get_subtasks",
        "create_subtask",
        "get_workspaces",
        "get_workspace",
        "get_projects",
        "get_project",
        "get_goals",
        "get_goal",
        "create_goal",
        "update_goal",
        "get_tags",
        "get_tag",
        "get_teams",
        "get_team",
        "get_users",
        "get_user",
        "get_sections",
        "get_section",
        "get_section_tasks",
        "get_time_periods",
        "get_goal_time_periods",
    )
