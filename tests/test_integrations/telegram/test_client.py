"""Synthetic only: no provider, credentials, hosted service or real durable DB."""

from __future__ import annotations

import unittest
from dataclasses import replace

from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedOperationResponse,
)

from zeo_integrations.telegram import TelegramClient, TelegramError


def confirmed(result, *, receipt=None):
    return HostedOperationResponse(
        status="confirmed",
        execution_id="synthetic-execution",
        result=result,
        receipt=receipt,
    )


def refused(condition=None, *, code="REQUEST_REFUSED", replayed=False, message="x"):
    receipt = {"replayed": replayed}
    if condition is not None:
        receipt["condition"] = condition
    return HostedOperationResponse(
        status="failed_safe",
        execution_id="synthetic-refusal",
        normalized_error={"code": code, "message": message},
        receipt=receipt,
    )


def batch(*, bot_id=7, cursor="opaque-issued", updates=None):
    return {
        "bot_id": bot_id,
        "fence": 2,
        "batch_cursor": cursor,
        "updates": updates if updates is not None else [
            {"update_id": 10, "message": {"text": "private fixture"}},
            {"update_id": 14, "callback_query": {"data": "opaque-action"}},
        ],
        "retention": {"state": "ok", "oldest_unacknowledged_age_seconds": None},
        "lost_to_retention": False,
    }


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, request):
        self.calls.append(request)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def fetch_artifact(self, **kwargs):
        raise AssertionError("receive slice must not fetch artifacts")


class Verifier:
    def __init__(self):
        self.accept = True
        self.calls = []

    def is_durably_handled(self, **kwargs):
        self.calls.append(kwargs)
        return self.accept


class TelegramClientTests(unittest.TestCase):
    def client(self, *responses):
        transport = Transport(*responses)
        verifier = Verifier()
        client = TelegramClient(
            HostedConnectionClient(transport=transport),
            connection_id="synthetic-connection",
            consumers=("agenda", "app"),
            verifier=verifier,
            clock=lambda: 1.0,
        )
        return client, transport, verifier

    def read(self, client):
        return client.read_updates(idempotency_key="read-one", deadline=10)

    def ack(self, client, value, key="ack-one"):
        return client.acknowledge(value, idempotency_key=key, deadline=10)

    def test_read_and_durable_all_consumer_ack(self):
        client, transport, verifier = self.client(
            confirmed(batch()),
            confirmed({"acknowledged": True, "confirmed_cursor": "confirmed"}),
        )
        value = self.read(client)
        result = self.ack(client, value)
        self.assertEqual(result.confirmed_cursor, "confirmed")
        self.assertEqual(
            verifier.calls,
            [{"bot_id": 7, "update_ids": (10, 14), "consumers": ("agenda", "app")}],
        )
        bodies = [call.model_dump(exclude_none=True) for call in transport.calls]
        self.assertEqual(bodies[0]["arguments"], {"max": 100})
        self.assertEqual(bodies[1]["arguments"], {"batch_cursor": "opaque-issued"})
        for body in bodies:
            self.assertNotIn("expect", body)
            self.assertNotIn("offset", body["arguments"])
            self.assertNotIn("fence", body["arguments"])

    def test_uncommitted_consumer_blocks_ack_and_forged_batch_is_rejected(self):
        client, transport, verifier = self.client(confirmed(batch()))
        value = self.read(client)
        verifier.accept = False
        with self.assertRaisesRegex(TelegramError, "PREFIX_NOT_DURABLE"):
            self.ack(client, value)
        with self.assertRaisesRegex(TelegramError, "UNISSUED_BATCH"):
            self.ack(client, replace(value, batch_cursor="invented"))
        self.assertEqual(len(transport.calls), 1)

    def test_sparse_ids_do_not_require_fabricated_missing_updates(self):
        client, _, _ = self.client(confirmed(batch()))
        self.assertEqual(self.read(client).update_ids, (10, 14))

    def test_payload_copy_and_repr_do_not_expose_or_mutate_raw_content(self):
        client, _, _ = self.client(confirmed(batch()))
        value = self.read(client)
        payload = value.updates[0].payload()
        payload["text"] = "changed outside batch"
        self.assertEqual(value.updates[0].payload()["text"], "private fixture")
        self.assertNotIn("private fixture", repr(value))
        self.assertNotIn("private fixture", repr(value.updates[0]))

    def test_empty_is_not_unavailable_and_cannot_be_acked(self):
        client, _, _ = self.client(confirmed(batch(cursor=None, updates=[])))
        value = self.read(client)
        self.assertEqual(value.updates, ())
        with self.assertRaisesRegex(TelegramError, "EMPTY_PREFIX"):
            self.ack(client, value)
        unavailable, _, _ = self.client(RuntimeError("private transport URL"))
        with self.assertRaises(TelegramError) as caught:
            self.read(unavailable)
        self.assertEqual(str(caught.exception), "UNAVAILABLE")
        self.assertNotIn("private", str(caught.exception))

    def test_refusal_condition_does_not_depend_on_human_message(self):
        for message in ("redacted", "translated explanation"):
            for condition in ("receive_conflict", "lease_lost", "cursor_invalid"):
                with self.subTest(message=message, condition=condition):
                    client, transport, _ = self.client(
                        refused(condition, message=message)
                    )
                    with self.assertRaises(TelegramError) as caught:
                        self.read(client)
                    self.assertEqual(caught.exception.condition.value, condition)
                    self.assertEqual(len(transport.calls), 1)

    def test_unknown_or_mismatched_condition_is_not_success(self):
        for response in (
            refused("invented"),
            refused("lease_lost", code="RATE_LIMITED"),
            refused("result_not_retained", replayed=False),
        ):
            client, _, _ = self.client(response)
            with self.assertRaises(TelegramError):
                self.read(client)

    def test_transient_replay_never_exposes_an_old_batch_or_retries(self):
        client, transport, _ = self.client(
            refused("result_not_retained", replayed=True)
        )
        with self.assertRaises(TelegramError) as caught:
            self.read(client)
        self.assertEqual(caught.exception.condition.value, "result_not_retained")
        self.assertEqual(len(transport.calls), 1)
        client, _, _ = self.client(
            confirmed(batch(), receipt={"replayed": True})
        )
        with self.assertRaisesRegex(TelegramError, "REPLAY_WITHOUT_BATCH"):
            self.read(client)

    def test_generic_kernel_refusal_has_no_invented_condition(self):
        client, _, _ = self.client(refused())
        with self.assertRaises(TelegramError) as caught:
            self.read(client)
        self.assertIsNone(caught.exception.condition)

    def test_invalid_limits_and_expired_deadline_never_invoke(self):
        client, transport, _ = self.client()
        for maximum in (-1, 0, True, 101):
            with self.subTest(maximum=maximum), self.assertRaises(TelegramError):
                client.read_updates(
                    maximum=maximum, idempotency_key="read", deadline=10
                )
        with self.assertRaises(TelegramError):
            client.read_updates(idempotency_key="read", deadline=1)
        self.assertEqual(transport.calls, [])

    def test_malformed_or_unsupported_update_prevents_cursor_use(self):
        for updates in (
            [{"update_id": 1, "edited_message": {}}],
            [{"update_id": True, "message": {}}],
            [{"update_id": 2, "message": {}}, {"update_id": 1, "message": {}}],
            [{"update_id": 1, "message": {}, "callback_query": {}}],
        ):
            client, _, _ = self.client(confirmed(batch(updates=updates)))
            with self.subTest(updates=updates), self.assertRaises(TelegramError):
                self.read(client)

    def test_bot_change_does_not_reset_stable_business_identity(self):
        client, _, _ = self.client(confirmed(batch()), confirmed(batch(bot_id=8)))
        self.read(client)
        with self.assertRaisesRegex(TelegramError, "BOT_CHANGED"):
            self.read(client)

    def test_ambiguous_ack_requires_original_batch_and_key(self):
        unknown = HostedOperationResponse(
            status="ambiguous", execution_id="synthetic-unknown",
            normalized_error={"code": "RESULT_AMBIGUOUS", "message": "unknown"},
        )
        client, transport, _ = self.client(
            confirmed(batch()), unknown,
            confirmed({"acknowledged": True, "confirmed_cursor": "confirmed"}),
        )
        value = self.read(client)
        with self.assertRaises(TelegramError) as caught:
            self.ack(client, value)
        self.assertTrue(caught.exception.outcome_unknown)
        with self.assertRaisesRegex(TelegramError, "RECONCILE_ORIGINAL"):
            self.ack(client, value, key="fresh-key")
        self.assertEqual(len(transport.calls), 2)
        self.ack(client, value)
        self.assertEqual(
            transport.calls[1].idempotency_key, transport.calls[2].idempotency_key
        )
        self.assertEqual(transport.calls[1].arguments, transport.calls[2].arguments)

    def test_malformed_success_after_ack_is_unknown_not_a_safe_retry(self):
        client, transport, _ = self.client(
            confirmed(batch()),
            confirmed({"acknowledged": True, "confirmed_cursor": 17}),
        )
        value = self.read(client)
        with self.assertRaises(TelegramError) as caught:
            self.ack(client, value)
        self.assertTrue(caught.exception.outcome_unknown)
        with self.assertRaisesRegex(TelegramError, "RECONCILE_ORIGINAL"):
            self.ack(client, value, key="fresh-key")
        self.assertEqual(len(transport.calls), 2)

    def test_crash_or_revoked_ack_does_not_turn_subsequent_read_into_ack(self):
        # A synthetic Broker retains confirmed=11, pending=15. Client requests
        # never carry either offset; only the Broker may choose confirmed.
        for failure in (
            RuntimeError("transport lost after pending intent"),
            refused(message="operation is unavailable"),
        ):
            client, transport, _ = self.client(
                confirmed(batch()), failure, confirmed(batch())
            )
            value = self.read(client)
            with self.assertRaises(TelegramError):
                self.ack(client, value)
            self.read(client)
            self.assertEqual(transport.calls[-1].operation_id, "telegram.updates.read")
            self.assertEqual(transport.calls[-1].arguments, {"max": 100})

    def test_rate_delay_is_typed_not_parsed_from_message(self):
        response = refused("rate_limited", code="RATE_LIMITED", message="wait 999")
        data = response.model_dump(mode="json")
        data["receipt"]["retry_after_seconds"] = 3
        client, transport, _ = self.client(HostedOperationResponse.model_validate(data))
        with self.assertRaises(TelegramError) as caught:
            self.read(client)
        self.assertEqual(caught.exception.retry_after_seconds, 3)
        self.assertEqual(len(transport.calls), 1)

    def test_response_size_ceiling_refuses_without_echo(self):
        client, _, _ = self.client(confirmed(batch()))
        client._max_bytes = 10
        with self.assertRaisesRegex(TelegramError, "UNAVAILABLE"):
            self.read(client)


if __name__ == "__main__":
    unittest.main()
