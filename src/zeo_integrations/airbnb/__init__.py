from zeo_integrations._http import Client as BaseClient

from ._ported import AirbnbClient


class Client(BaseClient):
    provider = "airbnb"
    implementation = AirbnbClient
    origins = ("https://www.airbnb.com",)
    operations = ("search", "get_listing_details")
