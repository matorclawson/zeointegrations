"""Bounded yelp operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import YelpClient


class Client(BaseClient):
    provider = "yelp"
    implementation = YelpClient
    origins = ("https://yelp-business-api.p.rapidapi.com",)
    operations = (
        "search_businesses",
        "get_business_details",
        "get_business_reviews",
        "get_business_menus",
    )
