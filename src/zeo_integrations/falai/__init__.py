"""Selected operations from pinned VeyraX; MIT. See NOTICE."""

from zeo_integrations._http import Client as BaseClient


class _Operations:
    def __init__(self, transport):
        self.http = transport

    def list_models(self, parameters: dict):
        return self.http.get("https://fal.ai/api/models", params=parameters).json()

    def model_schema(self, parameters: dict):
        return self.http.get(
            "https://fal.ai/api/openapi/queue/openapi.json", params=parameters
        ).json()


class Client(BaseClient):
    provider = "falai"
    implementation = _Operations
    origins = ("https://fal.ai",)
    operations = ("list_models", "model_schema")
