"""MIT port; VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df.
aci_server/integrations/airbnb/client.py; Copyright VeyraX contributors.
"""

import json
import logging
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup


def _discard_log():
    pass


logger = logging.getLogger(__name__)


class AirbnbClient:
    def __init__(self, transport):
        self.session = transport

    BASE_URL = "https://www.airbnb.com"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    def _build_search_url(
        self,
        location: str,
        place_id: str | None = None,
        checkin: str | None = None,
        checkout: str | None = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        pets: int = 0,
        min_price: int | None = None,
        max_price: int | None = None,
        cursor: str | None = None,
    ) -> str:
        search_url = f"{self.BASE_URL}/s/{urllib.parse.quote(location)}/homes"
        params = {}
        if place_id:
            params["place_id"] = place_id
        if checkin:
            params["checkin"] = checkin
        if checkout:
            params["checkout"] = checkout
        if adults > 0:
            params["adults"] = str(adults)
        if children > 0:
            params["children"] = str(children)
        if infants > 0:
            params["infants"] = str(infants)
        if pets > 0:
            params["pets"] = str(pets)
        if min_price is not None:
            params["price_min"] = str(min_price)
        if max_price is not None:
            params["price_max"] = str(max_price)
        if cursor:
            params["cursor"] = cursor
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{search_url}?{query_string}"
        return search_url

    def _build_listing_url(
        self,
        listing_id: str,
        checkin: str | None = None,
        checkout: str | None = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        pets: int = 0,
    ) -> str:
        listing_url = f"{self.BASE_URL}/rooms/{listing_id}"
        params = {}
        if checkin:
            params["check_in"] = checkin
        if checkout:
            params["check_out"] = checkout
        if adults > 0:
            params["adults"] = str(adults)
        if children > 0:
            params["children"] = str(children)
        if infants > 0:
            params["infants"] = str(infants)
        if pets > 0:
            params["pets"] = str(pets)
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            listing_url = f"{listing_url}?{query_string}"
        return listing_url

    def search(self, parameters: dict) -> dict[str, Any]:
        location = parameters.get("location")
        if not location:
            raise ValueError("Location is required for search")
        search_url = self._build_search_url(
            location=location,
            place_id=parameters.get("place_id"),
            checkin=parameters.get("checkin"),
            checkout=parameters.get("checkout"),
            adults=parameters.get("adults", 1),
            children=parameters.get("children", 0),
            infants=parameters.get("infants", 0),
            pets=parameters.get("pets", 0),
            min_price=parameters.get("min_price"),
            max_price=parameters.get("max_price"),
            cursor=parameters.get("cursor"),
        )
        response = self.session.get(search_url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        script_element = soup.select_one("#data-deferred-state-0")
        if not script_element:
            _discard_log()
            return {"search_url": search_url, "raw_data": None}
        client_data = json.loads(script_element.text)["niobeMinimalClientData"][0][1]
        return {"search_url": search_url, "raw_data": client_data}

    def get_listing_details(self, parameters: dict) -> dict[str, Any]:
        listing_id = parameters.get("id")
        if not listing_id:
            raise ValueError("Listing ID is required")
        listing_url = self._build_listing_url(
            listing_id=listing_id,
            checkin=parameters.get("checkin"),
            checkout=parameters.get("checkout"),
            adults=parameters.get("adults", 1),
            children=parameters.get("children", 0),
            infants=parameters.get("infants", 0),
            pets=parameters.get("pets", 0),
        )
        response = self.session.get(listing_url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        script_element = soup.select_one("#data-deferred-state-0")
        if not script_element:
            _discard_log()
            return {"listing_url": listing_url, "raw_data": None}
        client_data = json.loads(script_element.text)["niobeMinimalClientData"][0][1]
        return {"listing_url": listing_url, "raw_data": client_data}
