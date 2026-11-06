"""Selected operations from pinned VeyraX; MIT. See NOTICE."""

from zeo_integrations._http import Client as BaseClient


class _Operations:
    def __init__(self, transport):
        self.http = transport

    def list_resources(self, cloud_name: str, parameters: dict):
        return self.http.get(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/resources", params=parameters
        ).json()

    def get_resource(
        self,
        cloud_name: str,
        resource_type: str,
        delivery_type: str,
        public_id: str,
        parameters: dict,
    ):
        return self.http.get(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/resources/{resource_type}/{delivery_type}/{public_id}",
            params=parameters,
        ).json()


class Client(BaseClient):
    provider = "cloudinary"
    implementation = _Operations
    origins = ("https://api.cloudinary.com",)
    operations = ("list_resources", "get_resource")
