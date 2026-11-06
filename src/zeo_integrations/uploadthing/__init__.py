"""Bounded uploadthing operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import UploadThingClient


class Client(BaseClient):
    provider = "uploadthing"
    implementation = UploadThingClient
    origins = ("https://api.uploadthing.com",)
    operations = (
        "list_files",
        "poll_upload",
        "get_server_callback",
        "set_server_callback",
        "prepare_upload",
        "upload_files",
        "rename_files",
        "delete_files",
        "get_app_info",
        "get_usage_info",
    )
