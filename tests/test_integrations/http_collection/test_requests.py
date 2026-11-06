"""Pinned-source request vectors. These prove routing, not provider acceptance."""

import importlib
import json
from pathlib import Path

import pytest

from zeo_integrations._http import IntegrationError

VECTORS = json.loads(Path(__file__).with_name("request_vectors.json").read_text())


class StopAtDispatch:
    origin = "https://fixture.example"

    def __init__(self):
        self.requests = []

    def request(self, request):
        self.requests.append(
            {
                "method": request.method,
                "url": request.url,
                "query": request.query,
                "json_body": request.json_body,
                "form_body": request.form_body,
            }
        )
        raise RuntimeError("synthetic dispatch boundary")


@pytest.mark.parametrize(
    "vector", VECTORS, ids=lambda v: v["provider"] + "." + v["operation"]
)
def test_pinned_provider_request(vector):
    cls = importlib.import_module("zeo_integrations." + vector["provider"]).Client
    transport = StopAtDispatch()
    if vector["provider"] in {"http_request", "n8n"}:
        client = cls(transport, origin=transport.origin)
    else:
        client = cls(transport, configuration=vector["configuration"])
    with pytest.raises(IntegrationError):
        client.invoke(
            vector["operation"],
            vector["arguments"],
            idempotency_key="probe",
            allow_effect=True,
        )
    assert transport.requests == vector["requests"]
    assert len(transport.requests) == 1
