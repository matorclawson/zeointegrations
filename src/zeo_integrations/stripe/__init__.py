"Original read-only Stripe operations, API reference checked 2026-10-31. MIT."

from typing import Annotated

from pydantic import Field

from zeo_integrations._http import Client as BaseClient


class _Operations:
    def __init__(self, transport):
        self.http = transport

    def list_customers(
        self,
        limit: Annotated[int, Field(ge=1, le=100)] = 10,
        starting_after: str | None = None,
    ):
        query = {"limit": limit}
        if starting_after is not None:
            query["starting_after"] = starting_after
        return self.http.get("https://api.stripe.com/v1/customers", params=query).json()

    def retrieve_balance(self):
        return self.http.get("https://api.stripe.com/v1/balance").json()


class Client(BaseClient):
    provider = "stripe"
    implementation = _Operations
    operations = ("list_customers", "retrieve_balance")
    origins = ("https://api.stripe.com",)
