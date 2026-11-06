"""Bounded perplexity operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import PerplexityClient


class Client(BaseClient):
    provider = "perplexity"
    implementation = PerplexityClient
    origins = ("https://api.perplexity.ai",)
    operations = ()
