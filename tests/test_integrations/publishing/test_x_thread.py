"""Pure thread planning binds full approved content; no network or persistence."""

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from zeo_integrations._http import IntegrationError
from zeo_integrations.publishing.x_thread import XThread, XThreadPost, XThreadStep


def thread(last="second", account="42"):
    return XThread(
        account,
        (XThreadPost("first", ("11",)), XThreadPost(last, reply_to_prior_index=0)),
    )


def confirmed(step, post_id="100"):
    return XThreadStep(step.index, step.request_digest, post_id)


def test_whole_preview_is_canonical_and_covers_account_media_and_links():
    value = thread("完整 🌍\nsecond")
    rendered = value.rendering()
    assert json.loads(rendered) == {
        "version": 1,
        "provider": "x",
        "account_id": "42",
        "posts": [
            {"text": "first", "media_ids": ["11"], "reply_to_prior_index": None},
            {"text": "完整 🌍\nsecond", "media_ids": [], "reply_to_prior_index": 0},
        ],
    }
    assert "完整" in rendered and "🌍" in rendered
    assert value.digest == hashlib.sha256(rendered.encode()).hexdigest()
    assert thread().digest == thread().digest
    assert (
        value.digest != thread().digest
        and value.digest != thread("完整 🌍\nsecond", "43").digest
    )
    with pytest.raises(FrozenInstanceError):
        value.account_id = "43"
    with pytest.raises(FrozenInstanceError):
        value.posts[0].text = "changed"


def test_confirmed_prefix_allows_only_the_next_step():
    value = thread()
    post0, state0 = value.next_step(())
    assert state0.index == 0 and state0.returned_id is None
    assert post0.reply_to_id is None and post0.media_ids == ["11"]
    assert value.next_index((state0,)) is None
    states = (confirmed(state0),)
    assert value.next_index(states) == 1
    post1, state1 = value.next_step(states)
    assert post1.reply_to_id == "100" and state1.index == 1
    assert value.next_index((*states, state1)) is None
    assert value.next_step((*states, confirmed(state1, "101"))) is None
    # A generated per-call DTO does not share mutable media with the approved value.
    post0.media_ids.append("22")
    assert value.posts[0].media_ids == ("11",)
    assert value.next_step(())[0].media_ids == ["11"]


@pytest.mark.parametrize("returned", [None, "UNKNOWN"])
def test_unconfirmed_or_unknown_never_recreates_or_advances(returned):
    value = thread()
    _, state0 = value.next_step(())
    state = XThreadStep(0, state0.request_digest, returned)
    assert value.next_index((state,)) is None
    assert value.next_step((state,)) is None


def test_any_unknown_in_a_contiguous_prefix_stops_even_with_later_records():
    value = thread()
    _, state0 = value.next_step(())
    states = (
        XThreadStep(0, state0.request_digest, "UNKNOWN"),
        XThreadStep(1, "0" * 64, "123"),
    )
    assert value.next_index(states) is None


def test_replayed_step_from_another_account_or_later_edited_post_is_refused():
    _, state0 = thread().next_step(())
    state = confirmed(state0)
    for value in (thread(account="43"), thread(last="a different later post")):
        with pytest.raises(IntegrationError, match="BINDING"):
            value.next_index((state,))


def test_prefix_shape_and_actual_request_digest_are_required():
    value = thread()
    _, step = value.next_step(())
    for states in (
        (XThreadStep(1, step.request_digest, "100"),),
        (XThreadStep(0, "0" * 64, "100"),),
        (confirmed(step), confirmed(step)),
    ):
        with pytest.raises(IntegrationError):
            value.next_index(states)


def test_reply_resolution_preserves_returned_id_and_binds_actual_request():
    value = thread()
    _, state0 = value.next_step(())
    first = value.next_step((confirmed(state0, "100"),))
    second = value.next_step((confirmed(state0, "101"),))
    assert first[0].reply_to_id == "100" and second[0].reply_to_id == "101"
    assert first[1].request_digest != second[1].request_digest
    with pytest.raises(IntegrationError, match="BINDING"):
        value.next_index((confirmed(state0, "101"), confirmed(first[1], "200")))


def test_twenty_digit_receipt_is_preserved_but_unusable_reply_never_advances():
    value = thread()
    _, state0 = value.next_step(())
    state = confirmed(state0, "18446744073709551615")
    assert state.returned_id == "18446744073709551615"
    assert value.next_step((state,)) is None


@pytest.mark.parametrize(
    "posts",
    [
        (),
        (XThreadPost("one", reply_to_prior_index=0),),
        (XThreadPost("one"), XThreadPost("two")),
        (XThreadPost("one"), XThreadPost("two", reply_to_prior_index=1)),
        tuple(
            XThreadPost("x", reply_to_prior_index=i - 1 if i else None)
            for i in range(26)
        ),
    ],
)
def test_empty_disconnected_forward_or_oversized_thread_is_refused(posts):
    with pytest.raises(IntegrationError):
        XThread("42", posts)


def test_full_6000_byte_preview_limit_is_enforced_without_cutting():
    posts = tuple(
        XThreadPost("x" * 280, reply_to_prior_index=i - 1 if i else None)
        for i in range(25)
    )
    with pytest.raises(IntegrationError, match="PREVIEW_LIMIT"):
        XThread("42", posts)
    with pytest.raises(IntegrationError, match="PREVIEW_LIMIT"):
        XThread(
            "42",
            tuple(
                XThreadPost("🌍" * 280, reply_to_prior_index=i - 1 if i else None)
                for i in range(10)
            ),
        )
    value = XThread(
        "42",
        tuple(
            XThreadPost("x", reply_to_prior_index=i - 1 if i else None)
            for i in range(25)
        ),
    )
    assert len(value.posts) == 25 and len(value.rendering().encode()) < 6000


@pytest.mark.parametrize(
    "factory",
    [
        lambda: XThreadPost(""),
        lambda: XThreadPost("a", ("1", "1")),
        lambda: XThreadPost("a", ("1/evil",)),
        lambda: XThreadPost("a", ["1"]),
        lambda: XThreadPost("\ud800"),
        lambda: XThreadPost("a", reply_to_prior_index=True),
        lambda: XThreadStep(True, "0" * 64),
        lambda: XThreadStep(0, "not-a-digest"),
        lambda: XThreadStep(0, "0" * 64, "invalid"),
    ],
)
def test_mutable_or_malformed_values_are_refused(factory):
    with pytest.raises(IntegrationError):
        factory()


def test_branching_to_an_older_parent_is_not_a_chain():
    with pytest.raises(IntegrationError, match="THREAD_REPLY_LINK"):
        XThread(
            "42",
            (
                XThreadPost("first"),
                XThreadPost("second", reply_to_prior_index=0),
                XThreadPost("third", reply_to_prior_index=0),
            ),
        )
