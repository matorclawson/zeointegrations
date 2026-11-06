"""Bounded dropbox operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import DropboxClient


class Client(BaseClient):
    provider = "dropbox"
    implementation = DropboxClient
    origins = ("https://api.dropboxapi.com", "https://content.dropboxapi.com")
    operations = (
        "get_file_metadata",
        "create_folder",
        "download_file",
        "delete_file",
        "move_file",
        "create_shared_link",
        "search_files",
        "search_continue",
    )
