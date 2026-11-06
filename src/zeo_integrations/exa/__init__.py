"""Bounded exa operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ExaClient


class Client(BaseClient):
    provider = "exa"
    implementation = ExaClient
    origins = ("https://api.exa.ai",)
    operations = ("search", "get_contents", "find_similar")
