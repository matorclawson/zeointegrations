"""Bounded zillow operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ZillowClient


class Client(BaseClient):
    provider = "zillow"
    implementation = ZillowClient
    origins = ("https://zillow-com1.p.rapidapi.com",)
    operations = (
        "get_property",
        "search_properties",
        "get_zestimate",
        "get_zestimate_history",
        "get_price_and_tax_history",
        "get_property_comps",
        "get_property_value_range",
        "get_similar_properties",
        "get_similar_sales",
        "get_similar_rentals",
        "get_market_location",
        "get_market_data",
    )
