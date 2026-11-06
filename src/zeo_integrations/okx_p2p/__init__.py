"""Selected operations from pinned VeyraX; MIT. See NOTICE."""

from zeo_integrations._http import Client as BaseClient


class _Operations:
    def __init__(self, transport):
        self.http = transport

    def buy_offers(self, crypto: str, parameters: dict):
        return self.http.get(
            f"https://p2p-binance-api-p2p-okx-api-and-p2p-bybit-real-time-data.p.rapidapi.com/okx_sell/{crypto}",
            params=parameters,
        ).json()

    def sell_offers(self, crypto: str, parameters: dict):
        return self.http.get(
            f"https://p2p-binance-api-p2p-okx-api-and-p2p-bybit-real-time-data.p.rapidapi.com/okx_buy/{crypto}",
            params=parameters,
        ).json()


class Client(BaseClient):
    provider = "okx_p2p"
    implementation = _Operations
    origins = (
        (
            "https://p2p-binance-api-p2p-okx-api-and-p2p-bybit-real-time-"
            "data.p.rapidapi.com"
        ),
    )
    operations = ("buy_offers", "sell_offers")
