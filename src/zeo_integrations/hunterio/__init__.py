"""Bounded hunterio operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import HunterIOClient


class Client(BaseClient):
    provider = "hunterio"
    implementation = HunterIOClient
    origins = ("https://api.hunter.io",)
    operations = (
        "domain_search",
        "email_finder",
        "email_verifier",
        "email_count",
        "account_information",
        "email_enrichment",
        "company_enrichment",
        "combined_enrichment",
    )
