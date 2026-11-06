"""Bounded todoist operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TodoistClient


class Client(BaseClient):
    provider = "todoist"
    implementation = TodoistClient
    origins = ("https://api.todoist.com",)
    operations = (
        "get_projects",
        "create_project",
        "get_project",
        "update_project",
        "delete_project",
        "get_collaborators",
        "get_sections",
        "get_section",
        "create_section",
        "update_section",
        "delete_section",
        "get_tasks",
        "create_task",
        "get_task",
        "update_task",
        "close_task",
        "reopen_task",
        "delete_task",
        "get_comments",
        "create_comment",
        "get_comment",
        "update_comment",
        "delete_comment",
        "get_personal_labels",
        "create_personal_label",
        "get_personal_label",
        "update_personal_label",
        "delete_personal_label",
        "get_shared_labels",
        "rename_shared_label",
        "remove_shared_label",
    )
