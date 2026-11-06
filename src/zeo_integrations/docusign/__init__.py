"""Bounded docusign operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import DocuSignClient


class Client(BaseClient):
    provider = "docusign"
    implementation = DocuSignClient
    origins = ("https://account.docusign.com", "https://docusign.net")
    operations = (
        "get_user_info",
        "create_envelope",
        "get_envelope",
        "get_document",
        "create_recipient_view",
        "get_form_data",
        "get_envelopes",
    )
