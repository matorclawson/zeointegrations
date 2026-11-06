"""Bounded confluence operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ConfluenceClient


class Client(BaseClient):
    provider = "confluence"
    implementation = ConfluenceClient
    origins = ("https://api.atlassian.com",)
    operations = ("get_page", "create_page", "update_page", "delete_page")
