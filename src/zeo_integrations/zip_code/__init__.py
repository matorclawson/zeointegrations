"""Bounded zip_code operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ZipCodeClient


class Client(BaseClient):
    provider = "zip_code"
    implementation = ZipCodeClient
    origins = ("https://api.zippopotam.us",)
    operations = ("get_by_zipcode", "get_by_city")
