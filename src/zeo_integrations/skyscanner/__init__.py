"""Bounded skyscanner operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import SkyscannerClient


class Client(BaseClient):
    provider = "skyscanner"
    implementation = SkyscannerClient
    origins = ("https://sky-scanner3.p.rapidapi.com",)
    operations = (
        "search_everywhere",
        "search_roundtrip",
        "search_one_way",
        "get_flight_detail",
        "get_price_calendar",
        "get_price_calendar_return",
        "get_cheapest_one_way",
        "search_hotels",
        "get_hotel_detail",
        "get_hotel_prices",
        "get_hotel_reviews",
    )
