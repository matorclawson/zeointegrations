"""Bounded resend operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ResendClient


class Client(BaseClient):
    provider = "resend"
    implementation = ResendClient
    origins = ("https://api.resend.com",)
    operations = (
        "send_email",
        "send_batch_emails",
        "get_email",
        "update_email",
        "cancel_email",
        "create_domain",
        "get_domain",
        "verify_domain",
        "update_domain",
        "list_domains",
        "delete_domain",
        "create_broadcast",
        "get_broadcast",
        "send_broadcast",
        "delete_broadcast",
        "list_broadcasts",
        "create_audience",
        "get_audience",
        "delete_audience",
        "list_audiences",
        "create_contact",
        "get_contact",
        "update_contact",
        "delete_contact",
        "list_contacts",
    )
