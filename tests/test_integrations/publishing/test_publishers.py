"""Original synthetic wire tests. No account credentials or live publication."""

import httpx
import pytest

from zeo_integrations._http import HttpxTransport
from zeo_integrations.publishing import (
    InstagramMedia,
    InstagramPublisher,
    ThreadsMedia,
    ThreadsPublisher,
)


def wire(origin, handler):
    return HttpxTransport(transport=httpx.MockTransport(handler), origins=(origin,))


@pytest.mark.parametrize("kind", ["instagram", "threads"])
def test_container_is_not_publication(kind):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"id": "123"})

    cls = InstagramPublisher if kind == "instagram" else ThreadsPublisher
    with wire(cls.origin, handler) as transport:
        extra = {"api_version": "v23.0"} if kind == "instagram" else {}
        client = cls(
            transport,
            account_id="account",
            media_origins=("https://media.example",),
            **extra,
        )
        post = (
            InstagramMedia(media_type="IMAGE", media_url="https://media.example/a.jpg")
            if kind == "instagram"
            else ThreadsMedia(media_type="TEXT", text="hello")
        )
        assert (
            client.create_container(post, key="prepare", allow_effect=True)["stage"]
            == "processing"
        )
        assert len(seen) == 1
        assert (
            client.publish_container("123", key="publish", allow_effect=True)["stage"]
            == "published"
        )
    assert len(seen) == 2
    assert seen[1].content == b"creation_id=123"
