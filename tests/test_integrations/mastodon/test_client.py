"""Fake-only publishing boundaries; no provider credentials or network.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
"""

from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from traceback import format_exception

import pytest

from zeo_integrations.mastodon import (
    MastodonClient,
    MastodonError,
    MediaUpload,
    ReadyMedia,
    Response,
)

ORIGIN = "https://social.example"
BINDING = "opaque-connection-1"


def configuration(characters=500, image_bytes=100):
    return {
        "configuration": {
            "statuses": {
                "max_characters": characters,
                "max_media_attachments": 2,
                "characters_reserved_per_url": 23,
            },
            "media_attachments": {
                "supported_mime_types": ["image/png", "video/mp4", "audio/ogg"],
                "image_size_limit": image_bytes,
                "video_size_limit": 200,
                "description_limit": 30,
            },
        }
    }


def response(status=200, body=None, **kwargs):
    return Response(status, body, kwargs.pop("origin", ORIGIN), **kwargs)


def media_body(identity="42", url="https://cdn.example/file", kind="image"):
    return {"id": identity, "url": url, "type": kind}


class Clock:
    def __init__(self):
        self.current = 0.0
        self.sleeps = []

    def now(self):
        return self.current

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.current += seconds


class Transport:
    origin = ORIGIN
    binding = BINDING

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        upload = kwargs.get("upload")
        if upload is not None:
            content = bytearray()
            while chunk := upload.read(65536):
                content.extend(chunk)
            kwargs["uploaded_bytes"] = bytes(content)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def client(transport, **kwargs):
    clock = kwargs.pop("clock", Clock())
    return MastodonClient(
        transport,
        origin=ORIGIN,
        max_upload_bytes=300,
        monotonic=clock.now,
        wall_clock=lambda: 0.0,
        sleep=clock.sleep,
        **kwargs,
    )


def reply(status=200, body=None, **kwargs):
    return response(status, body, headers=kwargs.pop("headers", {}), **kwargs)


class FakeUploadSource:
    """Synthetic Broker-created source; deliberately exposes no seek/tell."""

    def __init__(self, data=b"png", **kwargs):
        self.size = kwargs.pop("size", len(data))
        self.filename = kwargs.pop("filename", "image.png")
        self.mime = kwargs.pop("mime_type", "image/png")
        self.sha256 = kwargs.pop("sha256", sha256(data).hexdigest())
        self._data = BytesIO(data)
        self.closed = False
        self.read_sizes = []

    def read(self, n):
        assert 0 < n <= 65536
        self.read_sizes.append(n)
        return self._data.read(n)

    def close(self):
        self.closed = True
        self._data.close()


def stream(data=b"png", **kwargs):
    description = kwargs.pop("description", "A helpful description")
    return MediaUpload(FakeUploadSource(data, **kwargs), description)


def publish(subject, **kwargs):
    return subject.publish_status(
        text=kwargs.pop("text", "hello"),
        visibility=kwargs.pop("visibility", "private"),
        idempotency_key=kwargs.pop("idempotency_key", "stable-operation-1"),
        **kwargs,
    )


def test_instance_specific_limits_without_default():
    a = client(Transport(reply(body=configuration(12, 40)))).discover_limits()
    b = client(Transport(reply(body=configuration(900, 90)))).discover_limits()
    assert (a.max_characters, a.image_size_limit) == (12, 40)
    assert (b.max_characters, b.image_size_limit) == (900, 90)


@pytest.mark.parametrize("bad", [None, {}, {"configuration": []}])
def test_missing_configuration_fails(bad):
    with pytest.raises(MastodonError, match="CONFIGURATION"):
        client(Transport(reply(body=bad))).discover_limits()


@pytest.mark.parametrize("bad", [True, 0, -1, "500"])
def test_malformed_limits_fail(bad):
    data = configuration()
    data["configuration"]["statuses"]["max_characters"] = bad
    with pytest.raises(MastodonError, match="CONFIGURATION"):
        client(Transport(reply(body=data))).discover_limits()


def test_upload_ready_and_caller_stream_stays_open():
    transport = Transport(reply(body=configuration()), reply(body=media_body()))
    item = stream()
    ready = client(transport).upload_media(item)
    assert ready == ReadyMedia("42", "https://cdn.example/file", ORIGIN, BINDING)
    assert transport.calls[1][2]["uploaded_bytes"] == b"png"
    assert transport.calls[1][2]["fields"] == {"description": item.description}
    assert not item.stream.closed
    assert transport.calls[1][2]["upload"].closed


def test_async_media_waits_for_processed_url():
    clock = Clock()
    transport = Transport(
        reply(body=configuration()),
        reply(202, media_body(url=None)),
        reply(206, media_body(url=None)),
        reply(body=media_body()),
    )
    assert client(transport, clock=clock).upload_media(stream()).id == "42"
    assert [m for m, _, _ in transport.calls] == ["GET", "POST", "GET", "GET"]
    assert clock.sleeps == [1.0]


@pytest.mark.parametrize(
    "status,body", [(422, {}), (200, media_body("43")), (200, media_body(url=None))]
)
def test_processing_failure_never_publishes(status, body):
    transport = Transport(
        reply(body=configuration()),
        reply(202, media_body(url=None)),
        reply(status, body),
    )
    with pytest.raises(MastodonError):
        client(transport).upload_media(stream())
    assert all(path != "/api/v1/statuses" for _, path, _ in transport.calls)


def test_processing_deadline_and_finite_poll_cap():
    transport = Transport(
        reply(body=configuration()),
        reply(202, media_body(url=None)),
        reply(206, media_body(url=None)),
    )
    with pytest.raises(MastodonError, match="DEADLINE"):
        client(transport, timeout_seconds=0.5).upload_media(stream())
    assert len(transport.calls) == 3


@pytest.mark.parametrize(
    "item",
    [
        stream(b"a" * 101),
        stream(description="a" * 31),
        stream(filename="bad\r\nfile"),
        stream(mime_type="image/x-unknown"),
    ],
)
def test_bad_upload_no_post(item):
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError):
        client(transport).upload_media(item)
    assert [m for m, _, _ in transport.calls] == ["GET"]


def test_unsupported_audio_does_not_guess_video_limit():
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError, match="UNSUPPORTED_MEDIA"):
        client(transport).upload_media(stream(mime_type="audio/ogg"))
    assert len(transport.calls) == 1


def test_status_exact_visibility_key_and_optional_fields():
    transport = Transport(
        reply(body=configuration()), reply(body={"id": "77", "url": ORIGIN + "/@me/77"})
    )
    result = publish(
        client(transport), spoiler_text="CW", sensitive=True, language="en"
    )
    assert result.id == "77"
    _, path, request = transport.calls[-1]
    assert path == "/api/v1/statuses"
    assert request["headers"] == {"Idempotency-Key": "stable-operation-1"}
    assert request["fields"] == {
        "status": "hello",
        "visibility": "private",
        "spoiler_text": "CW",
        "sensitive": True,
        "language": "en",
    }


@pytest.mark.parametrize(
    "changes",
    [
        dict(text="a" * 501),
        dict(visibility="default"),
        dict(idempotency_key="\r\ninjected"),
        dict(text=""),
    ],
)
def test_status_preflight_no_write(changes):
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError):
        publish(client(transport), **changes)
    assert len(transport.calls) == 1


def test_foreign_media_and_unfinished_receipts_cannot_publish():
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError, match="BINDING"):
        publish(
            client(transport),
            media=[
                ReadyMedia("42", "https://cdn.example/a", ORIGIN, "another-account")
            ],
        )
    assert len(transport.calls) == 1
    transport = Transport(reply(body=configuration()), reply(422, {}))
    with pytest.raises(MastodonError, match="PROCESSING"):
        publish(
            client(transport),
            media=[ReadyMedia("42", "https://cdn.example/a", ORIGIN, BINDING)],
        )
    assert not any(m == "POST" for m, _, _ in transport.calls)


def test_ready_media_id_rechecked_before_status_write():
    transport = Transport(
        reply(body=configuration()),
        reply(body=media_body()),
        reply(body={"id": "77", "url": ORIGIN + "/@me/77"}),
    )
    publish(
        client(transport),
        media=[ReadyMedia("42", "https://cdn.example/a", ORIGIN, BINDING)],
    )
    assert transport.calls[1][1] == "/api/v1/media/42"
    assert transport.calls[2][2]["fields"]["media_ids[]"] == ["42"]


@pytest.mark.parametrize("status", [401, 403])
def test_auth_never_retried(status):
    transport = Transport(reply(status, {"error": "secret-sentinel"}))
    with pytest.raises(MastodonError, match="AUTH"):
        client(transport).discover_limits()
    assert len(transport.calls) == 1


def test_read_429_observes_retry_after_then_succeeds():
    clock = Clock()
    transport = Transport(
        reply(429, {}, headers={"Retry-After": "3"}), reply(body=configuration())
    )
    client(transport, clock=clock).discover_limits()
    assert sum(clock.sleeps) == 3.0
    assert len(transport.calls) == 2


def test_reset_header_bounds_next_request():
    clock = Clock()
    transport = Transport(
        reply(
            body=configuration(),
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1970-01-01T00:00:03Z",
            },
        ),
        reply(body={"id": "77", "url": ORIGIN + "/@me/77"}),
    )
    subject = client(transport, clock=clock)
    subject.discover_limits()
    publish(subject)
    assert sum(clock.sleeps) == 3.0


@pytest.mark.parametrize(
    "failure,unknown",
    [
        (reply(429, {}), False),
        (reply(503, {}), True),
        (reply(body={}), True),
        (OSError("secret-sentinel"), True),
    ],
)
def test_status_failures_never_replay_or_leak(failure, unknown):
    transport = Transport(reply(body=configuration()), failure)
    with pytest.raises(MastodonError) as caught:
        publish(client(transport))
    assert caught.value.outcome_unknown is unknown
    assert len(transport.calls) == 2
    rendered = "".join(format_exception(caught.value))
    assert "secret-sentinel" not in rendered


def test_unknown_upload_is_never_replayed():
    transport = Transport(reply(body=configuration()), OSError("secret-sentinel"))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(stream())
    assert caught.value.outcome_unknown
    assert len(transport.calls) == 2
    assert "secret-sentinel" not in "".join(format_exception(caught.value))


@pytest.mark.parametrize(
    "result",
    [
        reply(302, {}),
        reply(body={}, redirected=True),
        reply(body=configuration(), origin="https://evil.example"),
    ],
)
def test_redirect_or_origin_drift_refused(result):
    transport = Transport(result)
    with pytest.raises(MastodonError):
        client(transport).discover_limits()
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    "origin",
    [
        "http://social.example",
        "https://u:p@social.example",
        ORIGIN + "/path",
        ORIGIN + "?query",
        "//social.example",
    ],
)
def test_unbound_origin_refused_before_request(origin):
    transport = Transport()
    with pytest.raises(MastodonError):
        MastodonClient(transport, origin=origin, max_upload_bytes=100)
    assert not transport.calls


def test_binding_mutation_refused_before_request():
    transport = Transport(reply(body=configuration()))
    subject = client(transport)
    subject.discover_limits()
    transport.binding = "another-account"
    with pytest.raises(MastodonError, match="BINDING"):
        publish(subject)
    assert len(transport.calls) == 1


def test_read_retry_bound_has_no_unbounded_loop():
    transport = Transport(reply(503, {}), reply(503, {}))
    with pytest.raises(MastodonError, match="READ_ATTEMPTS"):
        client(transport, max_read_attempts=2).discover_limits()
    assert len(transport.calls) == 2


def test_spoiler_and_url_reservation_participate_in_preflight():
    transport = Transport(reply(body=configuration(25)))
    with pytest.raises(MastodonError, match="STATUS_SIZE"):
        publish(client(transport), text="a.io", spoiler_text="warning")
    assert len(transport.calls) == 1


def test_absent_alt_limit_is_not_guessed():
    config = deepcopy(configuration())
    del config["configuration"]["media_attachments"]["description_limit"]
    with pytest.raises(MastodonError, match="CONFIGURATION"):
        client(Transport(reply(body=config))).discover_limits()


def test_http_date_retry_after_and_request_timeout_are_bounded():
    clock = Clock()
    transport = Transport(
        reply(429, {}, headers={"Retry-After": "Thu, 01 Jan 1970 00:00:02 GMT"}),
        reply(body=configuration()),
    )
    client(
        transport, clock=clock, timeout_seconds=5, request_timeout_seconds=3
    ).discover_limits()
    assert sum(clock.sleeps) == 2
    assert all(0 < call[2]["timeout_seconds"] <= 3 for call in transport.calls)


def test_fresh_import_needs_no_optional_sdk_or_network():
    import subprocess
    import sys

    source = """
import sys
import socket

def refused(*args, **kwargs):
    raise AssertionError("Unexpected network access during import")
socket.socket = refused
import zeo_integrations.mastodon
for name in ("requests", "httpx", "google", "hubspot", "mastodon"):
    assert name not in sys.modules, name
"""
    subprocess.run([sys.executable, "-I", "-c", source], check=True, timeout=10)


def test_upload_streamed_in_bounded_chunks_without_whole_file_read():
    class ChunkTransport(Transport):
        def request(self, method, path, **kwargs):
            upload = kwargs.get("upload")
            if upload:
                count = 0
                while chunk := upload.read(65536):
                    count += len(chunk)
                assert count == 131072
                self.calls.append((method, path, kwargs))
                return reply(body=media_body())
            return super().request(method, path, **kwargs)

    source = FakeUploadSource(b"a" * 131072, filename="big.png")
    transport = ChunkTransport(reply(body=configuration(image_bytes=200000)))
    subject = MastodonClient(transport, origin=ORIGIN, max_upload_bytes=200000)
    assert subject.upload_media(MediaUpload(source, "alt")).id == "42"
    assert len(source.read_sizes) == 3
    assert not source.closed


def test_broker_nonseekable_source_is_supported_without_seeking():
    source = FakeUploadSource()
    transport = Transport(reply(body=configuration()), reply(body=media_body()))
    assert client(transport).upload_media(MediaUpload(source, "alt")).id == "42"
    assert not hasattr(source, "seek")
    assert not source.closed


@pytest.mark.parametrize("operation", ["media", "status"])
@pytest.mark.parametrize("status", [408, 409, 418, 499, 503])
def test_post_ambiguous_status_never_replayed(operation, status):
    transport = Transport(reply(body=configuration()), reply(status, {}))
    with pytest.raises(MastodonError) as caught:
        subject = client(transport)
        if operation == "media":
            subject.upload_media(stream())
        else:
            publish(subject)
    assert caught.value.outcome_unknown
    assert caught.value.code == "OUTCOME_UNKNOWN"
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1


@pytest.mark.parametrize("status", [400, 404, 405, 406, 413, 415, 422, 429])
def test_closed_definite_refusals_have_known_outcome(status):
    transport = Transport(reply(body=configuration()), reply(status, {}))
    with pytest.raises(MastodonError) as caught:
        publish(client(transport))
    assert not caught.value.outcome_unknown
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1


@pytest.mark.parametrize("size", [2, 4])
def test_changed_upload_size_is_unknown_after_dispatch_and_not_replayed(size):
    item = stream(size=size)
    transport = Transport(reply(body=configuration()), reply(body=media_body()))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(item)
    assert caught.value.outcome_unknown
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1
    assert not item.source.closed


def test_invalid_declared_digest_refused_before_post():
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError, match="UPLOAD_SOURCE"):
        client(transport).upload_media(stream(sha256="invalid"))
    assert len(transport.calls) == 1


def test_mutated_source_metadata_refused_during_dispatch():
    class MutatingTransport(Transport):
        def request(self, method, path, **kwargs):
            if method == "POST":
                item.source.size += 1
            return super().request(method, path, **kwargs)

    item = stream()
    transport = MutatingTransport(reply(body=configuration()), reply(body=media_body()))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(item)
    assert caught.value.outcome_unknown
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1
    assert not item.source.closed


@pytest.mark.parametrize("declared_size", [True, 0, -1, 101])
def test_invalid_or_over_cap_declared_size_before_post(declared_size):
    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError):
        client(transport).upload_media(stream(size=declared_size))
    assert [method for method, _, _ in transport.calls] == ["GET"]


@pytest.mark.parametrize("declared_size", [2, 4])
def test_malformed_length_never_emits_past_declared_bound(declared_size):
    class RecordingTransport(Transport):
        def __init__(self, *answers):
            super().__init__(*answers)
            self.emitted = bytearray()

        def request(self, method, path, **kwargs):
            if method != "POST":
                return super().request(method, path, **kwargs)
            self.calls.append((method, path, kwargs))
            while chunk := kwargs["upload"].read(65536):
                self.emitted.extend(chunk)
            raise AssertionError("Malformed source must refuse")

    transport = RecordingTransport(reply(body=configuration()))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(stream(size=declared_size))
    assert caught.value.outcome_unknown
    assert len(transport.emitted) <= declared_size
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1


def test_source_violating_read_bound_cannot_emit_excess_bytes():
    class OversizedRead(FakeUploadSource):
        def read(self, n):
            return b"malformed-oversized-chunk"

    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(MediaUpload(OversizedRead(), "alt"))
    assert caught.value.outcome_unknown
    assert "uploaded_bytes" not in transport.calls[-1][2]


@pytest.mark.parametrize("malformed_eof", [None, "", bytearray()])
def test_nonbyte_eof_cannot_complete_upload(malformed_eof):
    class MalformedEOF(FakeUploadSource):
        def read(self, n):
            value = super().read(n)
            return value if value else malformed_eof

    transport = Transport(reply(body=configuration()))
    with pytest.raises(MastodonError) as caught:
        client(transport).upload_media(MediaUpload(MalformedEOF(), "alt"))
    assert caught.value.outcome_unknown
    assert sum(method == "POST" for method, _, _ in transport.calls) == 1
