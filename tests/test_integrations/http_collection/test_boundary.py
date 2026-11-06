"""Provider-independent failure and request qualification; no network."""

import importlib
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from zeo_integrations._http import IntegrationError, Response
from zeo_integrations.airtable import Client
from zeo_integrations.catalogue import providers
from zeo_integrations.database import Client as DatabaseClient
from zeo_integrations.database import Query
from zeo_integrations.ui import status_card


class Fake:
    def __init__(self, status=200, body=b'{"records": []}', redirect=False, fail=False):
        self.calls = []
        self.status, self.body, self.redirect, self.fail = status, body, redirect, fail

    def request(self, request):
        self.calls.append(request)
        if self.fail:
            raise RuntimeError("private-secret-do-not-leak")
        return Response(
            self.status,
            self.body,
            {},
            "https://wrong.example" if self.redirect else request.url,
        )


def test_airtable_exact_read():
    t = Fake()
    c = Client(t)
    assert c.invoke(
        "list_records",
        {
            "base_id": "base1",
            "table_id_or_name": "People",
            "params": {"maxRecords": 10},
        },
        idempotency_key="read-1",
    ) == {"records": []}
    q = t.calls[0]
    assert q.url == "https://api.airtable.com/v0/base1/People"
    assert q.method == "GET" and q.query == {"maxRecords": 10} and not q.effect
    assert all("authorization" != k.lower() for k in q.headers)


@pytest.mark.parametrize(
    "status,unknown",
    [
        (400, False),
        (401, False),
        (403, False),
        (429, False),
        (408, True),
        (500, True),
        (502, True),
    ],
)
def test_write_failure_is_never_retried(status, unknown):
    t = Fake(status=status)
    c = Client(t)
    with pytest.raises(IntegrationError) as e:
        c.invoke(
            "create_records",
            {"base_id": "base1", "table_id_or_name": "People", "data": {}},
            idempotency_key="write-1",
            allow_effect=True,
        )
    assert len(t.calls) == 1 and e.value.outcome_unknown is unknown
    assert t.calls[0].idempotency_key == "write-1"


@pytest.mark.parametrize(
    "options",
    [{"redirect": True}, {"fail": True}, {"body": b"not-json"}, {"body": b"x" * 2048}],
)
def test_uncertain_write_preserved_and_redacted(options):
    t = Fake(**options)
    c = Client(t, max_bytes=1024)
    with pytest.raises(IntegrationError) as e:
        c.invoke(
            "create_records",
            {"base_id": "base1", "table_id_or_name": "People", "data": {}},
            idempotency_key="write-1",
            allow_effect=True,
        )
    assert e.value.outcome_unknown and len(t.calls) == 1
    assert "private-secret" not in str(e.value)
    assert e.value.__context__ is None


@pytest.mark.parametrize(
    "args",
    [
        {"base_id": "../escape", "table_id_or_name": "People", "params": {}},
        {
            "base_id": "base1",
            "table_id_or_name": "People",
            "params": {"api_key": "private"},
        },
        {
            "base_id": "base1",
            "table_id_or_name": "People",
            "params": {},
            "unexpected": True,
        },
    ],
)
def test_bad_input_no_dispatch(args):
    t = Fake()
    with pytest.raises((IntegrationError, ValidationError)):
        Client(t).invoke("list_records", args, idempotency_key="k")
    assert not t.calls


def test_effect_refused_before_dispatch():
    t = Fake()
    with pytest.raises(IntegrationError):
        Client(t).invoke(
            "create_records",
            {"base_id": "base1", "table_id_or_name": "People", "data": {}},
            idempotency_key="k",
        )
    assert not t.calls


@pytest.mark.parametrize("name", sorted(providers()))
def test_every_catalogued_operation_has_closed_schema(name):
    entry = providers()[name]
    cls = importlib.import_module(entry["module"]).Client
    assert set(entry["operations"]) == set(cls.operations)
    for operation in cls.operations:
        schema = cls.input_model(operation).model_json_schema()
        assert schema["additionalProperties"] is False
        assert schema == entry["operations"][operation]["input_schema"]


def test_catalogue_import_is_lazy():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from zeo_integrations.catalogue import providers; "
                "providers(); assert 'zeo_integrations.airtable' not in sys.modules; "
                "assert 'requests' not in sys.modules"
            ),
        ],
        check=True,
    )


def test_data_only_core_card():
    card = status_card(
        provider="Airtable",
        operation="airtable.list_records",
        invocation="call:1",
        result_id="result:1",
        produced_at="2026-10-31T12:00:00Z",
        summary="Read completed",
        state="healthy",
    )
    assert card["components"][0]["props"]["action_refs"] == []
    with pytest.raises(ValueError):
        status_card(
            provider="x",
            operation="bad operation",
            invocation="call:1",
            result_id="result:1",
            produced_at="2026-10-31T12:00:00Z",
            summary="x",
        )


def test_database_real_sqlite_bounded_and_rollback():
    connection = sqlite3.connect(":memory:")
    client = DatabaseClient(connection, max_bytes=200)
    with pytest.raises(IntegrationError):
        client.execute(Query(statement="CREATE TABLE items (value TEXT)"))
    client.execute(
        Query(statement="CREATE TABLE items (value TEXT)"), allow_effect=True
    )
    client.execute(
        Query(statement="INSERT INTO items VALUES (?)", parameters=["one"]),
        allow_effect=True,
    )
    client.execute(
        Query(statement="INSERT INTO items VALUES (?)", parameters=["two"]),
        allow_effect=True,
    )
    result = client.execute(
        Query(statement="SELECT value FROM items", maximum_rows=1), allow_effect=True
    )
    assert result == {"columns": ["value"], "rows": [("one",)], "truncated": True}
    with pytest.raises(IntegrationError):
        client.execute(
            Query(
                statement="INSERT INTO items VALUES (?) RETURNING value",
                parameters=["x" * 500],
            ),
            allow_effect=True,
        )
    assert connection.execute("SELECT count(*) FROM items").fetchone()[0] == 2


def test_mail_partial_delivery_is_unknown():
    from zeo_integrations.mail import Client as MailClient
    from zeo_integrations.mail import Message

    smtp = SimpleNamespace(
        send_message=lambda *args, **kw: {"b@example.com": (550, b"refused")}
    )
    message = Message(
        sender="a@example.com",
        recipients=["b@example.com"],
        subject="Hello",
        text="Test",
    )
    with pytest.raises(IntegrationError) as e:
        MailClient(smtp).send(message, allow_effect=True)
    assert e.value.outcome_unknown


def test_amazon_sdk_adapter_bounds_and_redacts():
    from zeo_integrations.amazon import Client as AmazonClient
    from zeo_integrations.amazon import Search

    api = SimpleNamespace(search_items=lambda **kw: {"items": [{"id": "fixture"}]})
    assert (
        AmazonClient(api).search(Search(keywords="book"))["items"][0]["id"] == "fixture"
    )
    api.search_items = lambda **kw: {"items": "x" * 1048577}
    with pytest.raises(IntegrationError):
        AmazonClient(api).search(Search(keywords="book"))


def test_e2b_no_background_or_automatic_retry():
    from zeo_integrations.e2b import Client as E2BClient
    from zeo_integrations.e2b import Command

    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="ok", stderr="", exit_code=0)

    client = E2BClient(SimpleNamespace(commands=SimpleNamespace(run=run)))
    with pytest.raises(IntegrationError):
        client.run(Command(command="echo ok"))
    assert not calls
    assert client.run(Command(command="echo ok"), allow_effect=True)["exit_code"] == 0
    assert calls == [("echo ok", {"background": False, "timeout": 30})]


def test_whatsapp_acceptance_does_not_claim_delivery():
    from zeo_integrations.whatsapp import Client as WhatsAppClient
    from zeo_integrations.whatsapp import Message

    calls = []

    def send(*args, **kwargs):
        calls.append((args, kwargs))
        return True, "accepted"

    result = WhatsAppClient(send, user_id="fixture").send(
        Message(recipient="fixture", message="hello"), allow_effect=True
    )
    assert result == {"accepted_by_bridge": True, "delivered": None}
    assert len(calls) == 1


def test_sticky_transport_failure_cannot_be_swallowed_by_port():
    from zeo_integrations._http import Client as Base

    class Swallow:
        def __init__(self, transport):
            self.http = transport

        def run(self):
            try:
                self.http.get("https://fixture.example/read")
            except Exception:
                pass
            return {"ok": True}

    class Adapter(Base):
        provider = "fixture"
        implementation = Swallow
        operations = ("run",)
        origins = ("https://fixture.example",)

    with pytest.raises(IntegrationError):
        Adapter(Fake(fail=True)).invoke("run", {}, idempotency_key="k")


def test_multiple_calls_after_write_are_refused():
    from zeo_integrations._http import Client as Base

    class Double:
        def __init__(self, transport):
            self.http = transport

        def run(self):
            self.http.post("https://fixture.example/write")
            self.http.post("https://fixture.example/write")

    class Adapter(Base):
        provider = "fixture"
        implementation = Double
        operations = ("run",)
        origins = ("https://fixture.example",)

    transport = Fake()
    with pytest.raises(IntegrationError) as error:
        Adapter(transport).invoke("run", {}, idempotency_key="k", allow_effect=True)
    assert len(transport.calls) == 1 and error.value.outcome_unknown
