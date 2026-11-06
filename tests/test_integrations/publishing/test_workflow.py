from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedExpectedBinding,
    HostedOperationResponse,
)

from zeo_integrations.publishing.workflow import (
    Draft,
    Step,
    Target,
    WorkflowError,
    WorkflowRunner,
    WorkflowStore,
)

NOW = datetime(2026, 10, 31, 12, tzinfo=UTC)


class Broker:
    def __init__(self, answers):
        self.answers, self.requests = iter(answers), []

    def invoke(self, request):
        self.requests.append(request)
        result = next(self.answers)
        if isinstance(result, Exception):
            raise result
        return result


def confirmed(result):
    return HostedOperationResponse(
        status="confirmed", execution_id="test", result=result
    )


def target(name="x", steps=None):
    return Target(
        target_id=name,
        platform=name,
        connection_id="connection-" + name,
        expect=HostedExpectedBinding(external_identity=name, connection_revision="1"),
        caption="hello",
        steps=steps
        or [
            Step(
                step_id="publish",
                operation_id=name + ".publish",
                kind="effect",
                arguments={"text": "hello"},
            )
        ],
    )


def setup(tmp_path, targets=None):
    store = WorkflowStore(tmp_path / "workflow.sqlite")
    draft = Draft(title="Issue", scheduled_at=NOW, targets=targets or [target()])
    preview = store.save("org", "post", draft, actor="editor")
    return store, draft, preview


def runner(store, answers):
    broker = Broker(answers)
    return WorkflowRunner(store, HostedConnectionClient(transport=broker)), broker


def test_exact_approval_and_schedule(tmp_path):
    store, draft, preview = setup(tmp_path)
    run, broker = runner(store, [confirmed({"stage": "published", "post_id": "123"})])
    assert run.tick("org", now=NOW) is None
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    assert run.tick("org", now=NOW - timedelta(seconds=1)) is None
    assert run.tick("org", now=NOW)["state"] == "published"
    assert run.tick("org", now=NOW) is None
    assert len(broker.requests) == 1
    assert broker.requests[0].expect.external_identity == "x"


def test_edit_invalidates_approval_and_stale_preview(tmp_path):
    store, draft, preview = setup(tmp_path)
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    changed = draft.model_copy(update={"title": "Changed"})
    store.save("org", "post", changed, actor="editor", expected_revision=1)
    assert not store.preview("org", "post")["approved"]
    with pytest.raises(WorkflowError, match="preview changed"):
        store.approve("org", "post", actor="rod", digest=preview["digest"])
    with pytest.raises(WorkflowError, match="revision conflict"):
        store.save("org", "post", draft, actor="editor", expected_revision=1)


def test_crash_and_replay_uses_identical_request(tmp_path):
    store, _, preview = setup(tmp_path)
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    run, broker = runner(
        store, [TimeoutError("private"), confirmed({"stage": "published"})]
    )
    assert run.tick("org", now=NOW)["state"] == "unknown"
    assert run.tick("org", now=NOW) is None
    store = WorkflowStore(tmp_path / "workflow.sqlite")
    store.resume("org", "post", "x", actor="rod")
    run.store = store
    assert run.tick("org", now=NOW)["state"] == "published"
    assert broker.requests[0] == broker.requests[1]


def test_partial_failure_does_not_repeat_success(tmp_path):
    store, _, preview = setup(tmp_path, [target("a"), target("b")])
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    run, broker = runner(
        store,
        [
            confirmed({"stage": "published"}),
            TimeoutError(),
            confirmed({"stage": "published"}),
        ],
    )
    assert run.tick("org", now=NOW)["state"] == "published"
    assert run.tick("org", now=NOW)["state"] == "unknown"
    store.resume("org", "post", "b", actor="rod")
    run.tick("org", now=NOW)
    assert [r.connection_id for r in broker.requests] == [
        "connection-a",
        "connection-b",
        "connection-b",
    ]


def test_polling_checkpoints_and_fresh_read_keys(tmp_path):
    steps = [
        Step(step_id="create", operation_id="ig.create", kind="effect", arguments={}),
        Step(
            step_id="status",
            operation_id="ig.status",
            kind="read",
            arguments={"id": {"$step": "create", "field": "container_id"}},
            wait_field="status",
            ready_values=["FINISHED"],
            pending_values=["PROCESSING"],
        ),
        Step(
            step_id="publish",
            operation_id="ig.publish",
            kind="effect",
            arguments={"id": {"$step": "create", "field": "container_id"}},
        ),
    ]
    store, _, preview = setup(tmp_path, [target(steps=steps)])
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    run, broker = runner(
        store,
        [
            confirmed({"container_id": "123"}),
            confirmed({"status": "PROCESSING"}),
            confirmed({"status": "FINISHED"}),
            confirmed({"stage": "published"}),
        ],
    )
    assert run.tick("org", now=NOW)["state"] == "ready"
    assert run.tick("org", now=NOW)["state"] == "waiting"
    assert run.tick("org", now=NOW) is None
    assert run.tick("org", now=NOW + timedelta(seconds=60))["state"] == "ready"
    assert run.tick("org", now=NOW + timedelta(seconds=60))["state"] == "published"
    assert broker.requests[1].idempotency_key != broker.requests[2].idempotency_key
    assert broker.requests[3].arguments == {"id": "123"}


def test_two_workers_claim_once(tmp_path):
    store, _, preview = setup(tmp_path)
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    entered, release = Event(), Event()

    class SlowBroker:
        def invoke(self, request):
            entered.set()
            assert release.wait(10)
            return confirmed({"stage": "published"})

    run = WorkflowRunner(store, HostedConnectionClient(transport=SlowBroker()))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run.tick, "org", now=NOW)
        assert entered.wait(10)
        assert run.tick("org", now=NOW) is None
        store.recover("org", now=NOW + timedelta(seconds=121))
        assert run.tick("org", now=NOW + timedelta(seconds=122)) is None
        release.set()
        assert first.result()["state"] == "published"


def test_cancel_and_tenant_isolation(tmp_path):
    store, _, preview = setup(tmp_path)
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    with pytest.raises(WorkflowError):
        store.preview("other", "post")
    assert store.calendar("other", start=NOW, end=NOW + timedelta(days=1)) == []
    store.cancel("org", "post", actor="rod")
    run, broker = runner(store, [])
    assert run.tick("org", now=NOW) is None
    assert not broker.requests


def test_upload_acknowledgement_cannot_become_published(tmp_path):
    store, _, preview = setup(tmp_path)
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    run, _ = runner(store, [confirmed({"stage": "processing"})])
    assert run.tick("org", now=NOW)["state"] == "unknown"


def test_cancellation_during_media_resolution_prevents_dispatch(tmp_path):
    from zeo_integrations.publishing.workflow import Asset

    asset = Asset(
        asset_id="photo", sha256="a" * 64, media_type="image/png", size_bytes=10
    )
    t = target().model_copy(
        update={
            "asset_ids": ["photo"],
            "steps": [
                Step(
                    step_id="publish",
                    operation_id="x.publish",
                    kind="effect",
                    arguments={"url": {"$asset": "photo"}},
                )
            ],
        }
    )
    store = WorkflowStore(tmp_path / "workflow.sqlite")
    preview = store.save(
        "org",
        "post",
        Draft(title="Media", scheduled_at=NOW, assets=[asset], targets=[t]),
        actor="editor",
    )
    store.approve("org", "post", actor="rod", digest=preview["digest"])
    run, broker = runner(store, [])

    def resolve(asset):
        store.cancel("org", "post", actor="rod")
        return "https://media.example/a.png"

    run.media_url = resolve
    assert run.tick("org", now=NOW)["state"] == "cancelled"
    assert not broker.requests


def test_malformed_broker_response_stays_unknown(tmp_path):
    store, _, preview = setup(tmp_path)
    store.approve("org", "post", actor="editor", digest=preview["digest"])
    run, broker = runner(
        store, [{"status": "confirmed", "result": {"stage": "published"}}]
    )
    assert run.tick("org", now=NOW)["state"] == "unknown"
    assert run.tick("org", now=NOW) is None
    assert len(broker.requests) == 1
