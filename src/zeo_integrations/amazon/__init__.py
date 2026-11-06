"""Amazon PA-API through an externally authenticated SDK instance.

The injected SDK must disable retries and enforce request deadlines. MIT.
"""

import re
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError
from zeo_integrations._http.runtime import _bounded


class Search(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    keywords: str = Field(min_length=1, max_length=1024)


ASIN = Annotated[str, Field(pattern=r"^[A-Z0-9]{10}$")]


class Items(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    asins: list[ASIN] = Field(min_length=1, max_length=10)


class Variations(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    asin: ASIN


class BrowseNodes(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    browse_node_ids: list[Annotated[str, Field(pattern=r"^[0-9]{1,20}$")]] = Field(
        min_length=1, max_length=10
    )


def get_asin_from_url(url: str) -> str:
    """Extract a product ID locally; never resolve or fetch an arbitrary URL."""
    parsed = urlsplit(url)
    hosts = {
        "amazon.com",
        "amazon.co.uk",
        "amazon.de",
        "amazon.fr",
        "amazon.es",
        "amazon.it",
        "amazon.ca",
        "amazon.com.au",
        "amazon.co.jp",
        "amazon.in",
        "amazon.com.br",
        "amazon.com.mx",
        "amazon.nl",
        "amazon.se",
        "amazon.pl",
    }
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.hostname not in hosts | {"www." + host for host in hosts}
    ):
        raise IntegrationError("PRODUCT_URL")
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)", parsed.path)
    if match is None:
        raise IntegrationError("PRODUCT_URL")
    return match[1]


class Client:
    def __init__(self, amazon_api):
        self.api = amazon_api

    def search(self, query: Search):
        query = Search.model_validate(query.model_dump())
        return self._read(lambda: self.api.search_items(keywords=query.keywords))

    def get_items(self, query: Items):
        query = Items.model_validate(query.model_dump())
        return self._read(lambda: self.api.get_items(query.asins))

    def get_variations(self, query: Variations):
        query = Variations.model_validate(query.model_dump())
        return self._read(lambda: self.api.get_variations(query.asin))

    def get_browse_nodes(self, query: BrowseNodes):
        query = BrowseNodes.model_validate(query.model_dump())
        return self._read(lambda: self.api.get_browse_nodes(query.browse_node_ids))

    def _read(self, call):
        failed = False
        try:
            result = call()
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            if isinstance(result, list):
                result = [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in result
                ]
            _bounded(result, 1048576)
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("PROVIDER_RESPONSE")
        return result
