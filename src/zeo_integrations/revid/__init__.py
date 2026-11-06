"""Bounded revid operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import RevidAIClient


class Client(BaseClient):
    provider = "revid"
    implementation = RevidAIClient
    origins = ("https://www.revid.ai",)
    operations = (
        "create_video",
        "get_status",
        "get_projects",
        "add_to_queue",
        "publish_now",
    )
