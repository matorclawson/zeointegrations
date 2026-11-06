"""Bounded HTTP for a single origin explicitly admitted by Connect."""

from urllib.parse import urlsplit

from zeo_integrations._http import Client as BaseClient
from zeo_integrations._http import IntegrationError
from zeo_integrations._http.runtime import _url


class _Operations:
    def __init__(self, transport, origin: str):
        self.http, self.origin = transport, origin

    def get(self, path: str, parameters: dict):
        return self.http.get(self.origin + path, params=parameters).json()

    def post(self, path: str, body: dict):
        return self.http.post(self.origin + path, json=body).json()


class Client(BaseClient):
    provider = "http_request"
    implementation = _Operations
    operations = ("get", "post")
    origins = ()

    def __init__(self, transport, *, origin: str, **policy):
        if _url(origin) != origin or urlsplit(origin).path:
            raise IntegrationError("ORIGIN")
        if getattr(transport, "origin", None) != origin:
            raise IntegrationError("BINDING")
        self.origins = (origin,)
        super().__init__(transport, configuration={"origin": origin}, **policy)
