"""Bounded google_maps operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import GoogleMapsClient


class Client(BaseClient):
    provider = "google_maps"
    implementation = GoogleMapsClient
    origins = ("https://maps.googleapis.com",)
    operations = (
        "geocode",
        "reverse_geocode",
        "search_places",
        "place_details",
        "distance_matrix",
        "elevation",
        "directions",
    )
