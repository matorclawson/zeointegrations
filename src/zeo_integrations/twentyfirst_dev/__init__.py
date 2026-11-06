"""Bounded twentyfirst_dev operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TwentyFirstDevClient


class Client(BaseClient):
    provider = "twentyfirst_dev"
    implementation = TwentyFirstDevClient
    origins = ("https://21st.dev",)
    operations = ("search", "generate_prompt")
