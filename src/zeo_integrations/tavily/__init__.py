"""Bounded tavily operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TavilyClient


class Client(BaseClient):
    provider = "tavily"
    implementation = TavilyClient
    origins = ("https://api.tavily.com",)
    operations = ("search", "extract")
