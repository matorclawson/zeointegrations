"""Bounded duckduckgo operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import DuckDuckGoClient


class Client(BaseClient):
    provider = "duckduckgo"
    implementation = DuckDuckGoClient
    origins = ("https://api.duckduckgo.com",)
    operations = ("search",)
