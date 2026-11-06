"""Bounded readwise operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ReadwiseClient


class Client(BaseClient):
    provider = "readwise"
    implementation = ReadwiseClient
    origins = ("https://readwise.io",)
    operations = (
        "save_document",
        "list_documents",
        "update_document",
        "delete_document",
    )
