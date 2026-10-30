"""Synthetic only: no provider, credentials, hosted service or real durable DB."""

from __future__ import annotations

import unittest
from dataclasses import replace

from zeo_core.integrations.hosted.client import (
    HostedConnectionClient,
    HostedOperationResponse,
)

from zeo_integrations.telegram import TelegramClient, TelegramError


def confirmed(result, *, receipt=None, execution_id="synthetic-execution"):
    return HostedOperationResponse(
        status="confirmed",
        execution_id=execution_id,
        result=result,
        receipt={"condition": None, **(receipt or {})},
    )


def refused(condition=None, *, code="REQUEST_REFUSED", replayed=False, message="x"):
    receipt = {"replayed": replayed, "condition": condition}
    return HostedOperationResponse(
        status="failed_safe",
        execution_id="synthetic-refusal",
        normalized_error={"code": code, "message": message},
        receipt=receipt,
    )


def batch(*, bot_id=7, epoch=0, cursor="opaque-issued", updates=None):
    return {
        "bot_id": bot_id,
        "epoch": epoch,
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
            [{"batch": value, "consumers": ("agenda", "app")}],
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

    def test_changed_payload_requires_a_current_durable_disposition(self):
        changed = batch(updates=[
            {"update_id": 10, "message": {"text": "changed redelivery"}}
        ])
        client, transport, verifier = self.client(confirmed(changed))
        value = self.read(client)

        def check_current_batch(**kwargs):
            verifier.calls.append(kwargs)
            # Synthetic store knows the prior content for this stable ID.
            return kwargs["batch"].updates[0].payload()["text"] == "private fixture"

        verifier.is_durably_handled = check_current_batch
        with self.assertRaisesRegex(TelegramError, "PREFIX_NOT_DURABLE"):
            self.ack(client, value)
        self.assertIs(verifier.calls[0]["batch"], value)
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
            refused("result_not_retained"),
            refused("lease_lost", code="RATE_LIMITED"),
            refused("transient_replay", replayed=False),
        ):
            client, _, _ = self.client(response)
            with self.assertRaises(TelegramError):
                self.read(client)

    def test_transient_replay_never_exposes_an_old_batch_or_retries(self):
        client, transport, _ = self.client(
            refused("transient_replay", replayed=True)
        )
        with self.assertRaises(TelegramError) as caught:
            self.read(client)
        self.assertEqual(caught.exception.condition.value, "transient_replay")
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

    def test_required_null_condition_is_distinct_from_a_missing_field(self):
        client, _, _ = self.client(
            HostedOperationResponse(
                status="confirmed", execution_id="synthetic-missing",
                result=batch(), receipt={},
            )
        )
        with self.assertRaisesRegex(TelegramError, "INVALID_RECEIPT"):
            self.read(client)
        client, _, _ = self.client(confirmed(batch()))
        self.assertEqual(self.read(client).bot_id, 7)

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
            [{"update_id": 2, "message": {}}, {"update_id": 2, "message": {}}],
            [{"update_id": 1, "message": {}, "callback_query": {}}],
        ):
            client, _, _ = self.client(confirmed(batch(updates=updates)))
            with self.subTest(updates=updates), self.assertRaises(TelegramError):
                self.read(client)

    def test_reset_epoch_distinguishes_reused_id_and_identical_payload(self):
        client, _, _ = self.client(
            confirmed(batch(epoch=0)), confirmed(batch(epoch=1))
        )
        before = self.read(client)
        after = self.read(client)
        self.assertEqual(before.updates, after.updates)
        self.assertEqual(before.business_keys, ((7, 0, 10), (7, 0, 14)))
        self.assertEqual(after.business_keys, ((7, 1, 10), (7, 1, 14)))

    def test_fence_change_does_not_reset_business_dedup(self):
        newer = batch()
        newer["fence"] = 99
        client, _, _ = self.client(confirmed(batch()), confirmed(newer))
        before = self.read(client)
        after = self.read(client)
        self.assertEqual(before.business_keys, after.business_keys)

    def test_epoch_rollback_missing_or_boolean_epoch_is_unavailable(self):
        for invalid in (-1, True, None):
            client, _, _ = self.client(confirmed(batch(epoch=invalid)))
            with self.subTest(epoch=invalid), self.assertRaises(TelegramError):
                self.read(client)
        client, _, _ = self.client(
            confirmed(batch(epoch=2)), confirmed(batch(epoch=1))
        )
        self.read(client)
        with self.assertRaisesRegex(TelegramError, "EPOCH_REGRESSED"):
            self.read(client)

    def test_delivery_order_is_not_manufactured_from_numeric_ids(self):
        rows = [{"update_id": 9, "message": {}}, {"update_id": 2, "message": {}}]
        client, _, _ = self.client(confirmed(batch(updates=rows)))
        self.assertEqual(self.read(client).update_ids, (9, 2))

    def test_empty_recorded_drop_boundary_still_requires_durable_prefix(self):
        client, transport, verifier = self.client(
            confirmed(batch(updates=[])),
            confirmed({"acknowledged": True, "confirmed_cursor": "confirmed"}),
        )
        value = self.read(client)
        verifier.accept = False
        with self.assertRaisesRegex(TelegramError, "PREFIX_NOT_DURABLE"):
            self.ack(client, value)
        self.assertEqual(len(transport.calls), 1)
        verifier.accept = True
        self.ack(client, value)
        self.assertEqual(
            transport.calls[-1].arguments, {"batch_cursor": "opaque-issued"}
        )

    def test_bot_change_does_not_reset_stable_business_identity(self):
        client, _, _ = self.client(confirmed(batch()), confirmed(batch(bot_id=8)))
        self.read(client)
        with self.assertRaisesRegex(TelegramError, "BOT_CHANGED"):
            self.read(client)

    def test_ambiguous_ack_requires_original_batch_and_key(self):
        unknown = HostedOperationResponse(
            status="ambiguous", execution_id="synthetic-unknown",
            receipt={"condition": None},
            normalized_error={"code": "RESULT_AMBIGUOUS", "message": "unknown"},
        )
        client, transport, _ = self.client(
            confirmed(batch()), unknown,
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "confirmed"},
                execution_id="synthetic-unknown",
            ),
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

    def recovery_responses(self, final):
        first = HostedOperationResponse(
            status="ambiguous", execution_id="execution-E1",
            normalized_error={"code": "RESULT_AMBIGUOUS", "message": "unknown"},
            receipt={"condition": None},
        )
        stale = refused("cursor_stale").model_dump(mode="json")
        stale["receipt"]["pending_ack"] = {
            "state": "unresolved_stale", "execution_id": "execution-E1"
        }
        second_batch = batch(epoch=1, cursor="cursor-C2")
        second = confirmed(
            second_batch,
            receipt={
                "pending_ack": {
                    "state": "unresolved_stale", "execution_id": "execution-E1"
                },
                "recovery": {"open": True, "supersedes": "execution-E1"},
            },
        )
        return [
            confirmed(batch()), first,
            HostedOperationResponse.model_validate(stale), second, final,
        ], first

    def enter_recovery(self, client):
        original = self.read(client)
        with self.assertRaises(TelegramError) as ambiguous:
            self.ack(client, original, key="key-K1")
        self.assertTrue(ambiguous.exception.outcome_unknown)
        with self.assertRaises(TelegramError) as stale:
            self.ack(client, original, key="key-K1")
        self.assertEqual(stale.exception.condition.value, "cursor_stale")
        self.assertEqual(stale.exception.pending_execution_id, "execution-E1")
        return self.read(client)

    def test_linked_recovery_is_explicit_new_operation_not_old_resolution(self):
        responses, original_receipt = self.recovery_responses(
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "confirmed-C2"},
                execution_id="execution-E2",
            )
        )
        before = original_receipt.model_dump(mode="json")
        client, transport, _ = self.client(*responses)
        fresh = self.enter_recovery(client)
        with self.assertRaisesRegex(TelegramError, "RECONCILE_ORIGINAL"):
            self.ack(client, fresh, key="key-K1")
        with self.assertRaisesRegex(TelegramError, "RECOVERY_REQUIRES_NEW_KEY"):
            client.acknowledge_recovery(
                fresh, idempotency_key="key-K1", deadline=10
            )
        self.assertEqual(len(transport.calls), 4)
        result = client.acknowledge_recovery(
            fresh, idempotency_key="key-K2", deadline=10
        )
        self.assertEqual(result.execution_id, "execution-E2")
        self.assertEqual(result.superseded_execution_ids, ("execution-E1",))
        self.assertEqual(
            transport.calls[-1].arguments,
            {
                "batch_cursor": "cursor-C2",
                "supersedes_execution_id": "execution-E1",
            },
        )
        self.assertEqual(original_receipt.model_dump(mode="json"), before)

    def test_lost_linked_reply_resends_exact_original_new_body_and_key(self):
        responses, _ = self.recovery_responses(RuntimeError("lost E2 reply"))
        responses.append(confirmed(
            {"acknowledged": True, "confirmed_cursor": "confirmed-C2"},
            receipt={"replayed": True},
            execution_id="execution-E2",
        ))
        client, transport, _ = self.client(*responses)
        fresh = self.enter_recovery(client)
        with self.assertRaises(TelegramError) as lost:
            client.acknowledge_recovery(
                fresh, idempotency_key="key-K2", deadline=10
            )
        self.assertTrue(lost.exception.outcome_unknown)
        with self.assertRaises(TelegramError):
            self.ack(client, fresh, key="different-key")
        result = self.ack(client, fresh, key="key-K2")
        self.assertTrue(result.replayed)
        self.assertEqual(result.superseded_execution_ids, ("execution-E1",))
        self.assertEqual(transport.calls[-2].arguments, transport.calls[-1].arguments)
        self.assertEqual(
            transport.calls[-2].idempotency_key, transport.calls[-1].idempotency_key
        )

    def test_known_stale_original_is_not_resent_even_with_its_old_key(self):
        responses, _ = self.recovery_responses(
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "confirmed-C2"},
                execution_id="execution-E2",
            )
        )
        client, transport, _ = self.client(*responses)
        original = self.read(client)
        with self.assertRaises(TelegramError):
            self.ack(client, original, key="key-K1")
        with self.assertRaises(TelegramError):
            self.ack(client, original, key="key-K1")
        self.assertEqual(len(transport.calls), 3)
        with self.assertRaisesRegex(TelegramError, "RECOVERY_REQUIRED"):
            self.ack(client, original, key="key-K1")
        self.assertEqual(len(transport.calls), 3)
        fresh = self.read(client)
        client.acknowledge_recovery(
            fresh, idempotency_key="key-K2", deadline=10
        )

    def test_recovery_needs_issued_batch_and_current_durable_prefix(self):
        responses, _ = self.recovery_responses(
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "confirmed-C2"},
                execution_id="execution-E2",
            )
        )
        client, transport, verifier = self.client(*responses)
        fresh = self.enter_recovery(client)
        with self.assertRaisesRegex(TelegramError, "RECOVERY_NOT_GRANTED"):
            client.acknowledge_recovery(
                replace(fresh, recovery_execution_id="invented"),
                idempotency_key="key-K2", deadline=10,
            )
        verifier.accept = False
        with self.assertRaisesRegex(TelegramError, "PREFIX_NOT_DURABLE"):
            client.acknowledge_recovery(
                fresh, idempotency_key="key-K2", deadline=10
            )
        self.assertEqual(len(transport.calls), 4)
        verifier.accept = True
        client.acknowledge_recovery(
            fresh, idempotency_key="key-K2", deadline=10
        )

    def test_unlinked_ack_does_not_bypass_broker_recovery_context(self):
        response = confirmed(
            batch(epoch=1, cursor="cursor-C2"),
            receipt={"recovery": {"open": True, "supersedes": "execution-E1"}},
        )
        client, transport, _ = self.client(
            response,
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "confirmed-C2"},
                execution_id="execution-E2",
            ),
        )
        fresh = self.read(client)
        with self.assertRaisesRegex(TelegramError, "RECOVERY_REQUIRED"):
            self.ack(client, fresh, key="key-K2")
        self.assertEqual(len(transport.calls), 1)
        linked = client.acknowledge_recovery(
            fresh, idempotency_key="key-K2", deadline=10
        )
        self.assertEqual(linked.superseded_execution_ids, ("execution-E1",))

    def test_malformed_or_mismatched_recovery_metadata_cannot_authorize(self):
        receipts = [
            {"recovery": {"open": False, "supersedes": "execution-E1"}},
            {"pending_ack": {"state": "invented", "execution_id": "execution-E1"}},
            {
                "pending_ack": {
                    "state": "unresolved_stale", "execution_id": "execution-E1"
                },
                "recovery": {"open": True, "supersedes": "execution-E9"},
            },
        ]
        for receipt in receipts:
            client, transport, _ = self.client(
                confirmed(batch(epoch=1), receipt=receipt)
            )
            with self.subTest(receipt=receipt), self.assertRaises(TelegramError):
                self.read(client)
            self.assertEqual(len(transport.calls), 1)

    def test_wrong_open_intent_refuses_without_new_effect(self):
        responses, _ = self.recovery_responses(
            confirmed({"acknowledged": True, "confirmed_cursor": "unused"})
        )
        wrong = confirmed(
            batch(epoch=1),
            receipt={"recovery": {"open": True, "supersedes": "execution-E9"}},
        )
        responses[3] = wrong
        client, transport, _ = self.client(*responses)
        fresh = self.enter_recovery(client)
        with self.assertRaisesRegex(TelegramError, "PENDING_INTENT_MISMATCH"):
            client.acknowledge_recovery(
                fresh, idempotency_key="key-K2", deadline=10
            )
        self.assertEqual(len(transport.calls), 4)

    def test_linked_confirmation_cannot_reuse_the_old_execution_identity(self):
        responses, _ = self.recovery_responses(
            confirmed(
                {"acknowledged": True, "confirmed_cursor": "bad-link"},
                execution_id="execution-E1",
            )
        )
        client, transport, _ = self.client(*responses)
        fresh = self.enter_recovery(client)
        with self.assertRaises(TelegramError) as caught:
            client.acknowledge_recovery(
                fresh, idempotency_key="key-K2", deadline=10
            )
        self.assertTrue(caught.exception.outcome_unknown)
        with self.assertRaisesRegex(TelegramError, "RECONCILE_ORIGINAL"):
            self.ack(client, fresh, key="key-K3")
        self.assertEqual(len(transport.calls), 5)

    def test_recovery_condition_status_and_code_are_closed(self):
        for condition in ("cursor_stale", "recovery_required"):
            response = refused(condition)
            client, _, _ = self.client(confirmed(batch()), response)
            value = self.read(client)
            with self.assertRaises(TelegramError) as caught:
                self.ack(client, value)
            self.assertEqual(caught.exception.condition.value, condition)
            bad = response.model_dump(mode="json")
            bad["status"] = "refused"
            client, _, _ = self.client(
                HostedOperationResponse.model_validate(bad)
            )
            with self.assertRaisesRegex(TelegramError, "INVALID_RECEIPT"):
                self.read(client)

    def test_response_size_ceiling_refuses_without_echo(self):
        client, _, _ = self.client(confirmed(batch()))
        client._max_bytes = 10
        with self.assertRaisesRegex(TelegramError, "UNAVAILABLE"):
            self.read(client)


if __name__ == "__main__":
    unittest.main()
