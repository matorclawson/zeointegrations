"""Bounded firecrawl operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import FirecrawlClient


class Client(BaseClient):
    provider = "firecrawl"
    implementation = FirecrawlClient
    origins = ("https://api.firecrawl.dev",)
    operations = (
        "get_batch_status",
        "get_batch_errors",
        "get_crawl_status",
        "cancel_crawl",
        "get_crawl_errors",
        "get_extract_status",
        "get_credit_usage",
    )
