"""Bounded dub operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import DubClient


class Client(BaseClient):
    provider = "dub"
    implementation = DubClient
    origins = ("https://api.dub.co",)
    operations = (
        "create_link",
        "update_link",
        "upsert_link",
        "delete_link",
        "get_link_info",
        "get_links",
        "get_links_count",
        "bulk_create_links",
        "bulk_update_links",
        "bulk_delete_links",
        "get_qr_code",
        "get_analytics",
        "get_events",
        "get_customer",
        "get_customers",
        "update_customer",
        "delete_customer",
        "track_lead",
        "track_sale",
        "create_tag",
        "get_tags",
        "update_tag",
        "create_domain",
        "update_domain",
        "delete_domain",
        "get_domains",
        "get_workspace",
        "update_workspace",
    )
