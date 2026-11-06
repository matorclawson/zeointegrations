"""Bounded airtable operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import AirtableClient


class Client(BaseClient):
    provider = "airtable"
    implementation = AirtableClient
    origins = ("https://api.airtable.com", "https://content.airtable.com")
    operations = (
        "list_records",
        "get_record",
        "create_records",
        "update_records",
        "update_record",
        "delete_records",
        "delete_record",
        "upload_attachment",
        "sync_csv",
        "create_field",
        "update_field",
        "create_table",
        "update_table",
        "list_bases",
        "get_base_schema",
        "create_base",
        "list_webhooks",
        "create_webhook",
        "delete_webhook",
        "list_webhook_payloads",
        "get_user_info",
    )
