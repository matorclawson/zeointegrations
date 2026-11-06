"n8n workflow operations on an explicitly bound origin, no API key handling."

from zeo_integrations.http_request import Client as BoundClient


class _Operations:
    def __init__(self, transport, origin: str):
        self.http, self.origin = transport, origin

    def list_workflows(self, parameters: dict):
        return self.http.get(
            self.origin + "/api/v1/workflows", params=parameters
        ).json()

    def get_workflow(self, workflow_id: str):
        return self.http.get(self.origin + f"/api/v1/workflows/{workflow_id}").json()

    def create_workflow(self, body: dict):
        return self.http.post(self.origin + "/api/v1/workflows", json=body).json()

    def activate_workflow(self, workflow_id: str):
        return self.http.post(
            self.origin + f"/api/v1/workflows/{workflow_id}/activate"
        ).json()


class Client(BoundClient):
    provider = "n8n"
    implementation = _Operations
    operations = (
        "list_workflows",
        "get_workflow",
        "create_workflow",
        "activate_workflow",
    )
