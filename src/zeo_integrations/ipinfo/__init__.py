"""Bounded ipinfo operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import IpInfoClient


class Client(BaseClient):
    provider = "ipinfo"
    implementation = IpInfoClient
    origins = ("https://ipinfo.io",)
    operations = ("get_ip_info", "get_bulk_info", "get_asn_info")
