"""Bounded outlook operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import OutlookClient


class Client(BaseClient):
    provider = "outlook"
    implementation = OutlookClient
    origins = ("https://graph.microsoft.com",)
    operations = (
        "get_message",
        "create_draft",
        "delete_message",
        "send_message",
        "update_message",
        "list_calendars",
        "get_event",
        "create_event",
        "update_event",
        "delete_event",
    )
