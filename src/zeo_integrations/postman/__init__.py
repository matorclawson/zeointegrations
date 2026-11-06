"""Bounded postman operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import PostmanClient


class Client(BaseClient):
    provider = "postman"
    implementation = PostmanClient
    origins = ("https://api.getpostman.com",)
    operations = (
        "get_collections",
        "get_collection",
        "update_collection",
        "delete_collection",
        "create_collection",
        "get_environments",
        "get_environment",
        "create_environment",
        "update_environment",
        "delete_environment",
        "fork_collection",
        "get_workspaces",
        "get_workspace",
        "create_workspace",
        "update_workspace",
        "delete_workspace",
    )
