"""Bounded apollo operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ApolloClient


class Client(BaseClient):
    provider = "apollo"
    implementation = ApolloClient
    origins = ("https://apollo-io-no-cookies-required.p.rapidapi.com",)
    operations = (
        "search_people",
        "search_people_by_url",
        "search_organizations",
        "search_organizations_by_url",
        "get_person_details",
        "get_organization_details",
    )
