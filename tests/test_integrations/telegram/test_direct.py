"""Offline Bot API protocol and failure controls; only inert fixture tokens."""

import asyncio
import io
import json
import logging
import unittest

import httpx
from pydantic import SecretStr, ValidationError

from zeo_integrations.telegram.direct import (
    TelegramClient as TelegramBotClient,
)
from zeo_integrations.telegram.direct import (
    TelegramError,
)
from zeo_integrations.telegram.direct_models import (
    GetUpdatesRequest,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    SendMessageRequest,
    TelegramCredentials,
    TelegramOptions,
)

TOKEN = "123456:" + "a" * 35
CHAT = 1234


def message(**changes):
    return {
        "message_id": 5,
        "date": 1700000000,
        "chat": {"id": CHAT, "type": "private"},
        "from": {"id": CHAT, "is_bot": False, "first_name": "Fixture"},
        "text": "private example",
        **changes,
    }


class ClientTests(unittest.IsolatedAsyncioTestCase):
    def client(self, handler, **kwargs):
        client = TelegramBotClient(
            TOKEN, transport=httpx.MockTransport(handler), **kwargs
        )
        self.addAsyncCleanup(client.aclose)
        return client

    async def test_poll_exact_request_and_typed_message(self):
        calls = []

        def handle(request):
            calls.append(request)
            self.assertEqual(request.method, "POST")
            self.assertEqual(
                str(request.url), f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            )
            data = json.loads(request.content)
            self.assertEqual(
                data,
                {
                    "limit": 100,
                    "timeout": 20,
                    "allowed_updates": ["message", "callback_query"],
                },
            )
            return httpx.Response(
                200,
                json={"ok": True, "result": [{"update_id": 10, "message": message()}]},
            )

        rows = await self.client(handle).get_updates()
        self.assertEqual(rows[0].message.from_user.id, CHAT)
        self.assertEqual(rows[0].message.chat.type, "private")
        self.assertEqual(rows[0].message.date, 1700000000)
        self.assertEqual(rows[0].kind, "message")
        self.assertEqual(len(calls), 1)
        self.assertNotIn("private example", repr(rows))

    async def test_explicit_offset_no_implicit_page_loop(self):
        seen = []

        def handle(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200, json={"ok": True, "result": [{"update_id": 11}]})

        rows = await self.client(handle).get_updates(offset=11, limit=1)
        self.assertEqual(seen[0]["offset"], 11)
        self.assertEqual(rows[0].kind, "unsupported")
        self.assertEqual(len(seen), 1)

    async def test_callback_sender_and_data_preserved(self):
        callback = {
            "id": "opaque",
            "from": {"id": CHAT, "is_bot": False, "first_name": "Fixture"},
            "chat_instance": "instance",
            "message": message(),
            "data": "order-review",
        }
        rows = await self.client(
            lambda request: httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": [{"update_id": 12, "callback_query": callback}],
                },
            )
        ).get_updates()
        self.assertEqual(rows[0].kind, "callback_query")
        self.assertEqual(rows[0].callback_query.data, "order-review")
        self.assertNotIn("order-review", repr(rows))

    async def test_send_and_inline_keyboard_native_shape(self):
        def handle(request):
            self.assertTrue(request.url.path.endswith("/sendMessage"))
            data = json.loads(request.content)
            self.assertEqual(
                data,
                {
                    "chat_id": CHAT,
                    "text": "hello",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "Confirm", "callback_data": "draft-v1"}]
                        ]
                    },
                },
            )
            return httpx.Response(200, json={"ok": True, "result": message()})

        request = SendMessageRequest(
            chat_id=CHAT,
            text="hello",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=(
                    (InlineKeyboardButton(text="Confirm", callback_data="draft-v1"),),
                )
            ),
        )
        sent = await self.client(handle).send_message(
            request.chat_id, request.text, reply_markup=request.reply_markup
        )
        self.assertEqual(sent.message_id, 5)

    async def test_callback_answer_does_not_send_business_action(self):
        def handle(request):
            self.assertTrue(request.url.path.endswith("/answerCallbackQuery"))
            self.assertEqual(
                json.loads(request.content),
                {"callback_query_id": "opaque", "show_alert": False, "cache_time": 0},
            )
            return httpx.Response(200, json={"ok": True, "result": True})

        self.assertIs(await self.client(handle).answer_callback_query("opaque"), True)

    async def test_strict_request_boundaries(self):
        bad = [
            lambda: GetUpdatesRequest(offset=-1),
            lambda: GetUpdatesRequest(limit=True),
            lambda: SendMessageRequest(chat_id="1234", text="hi"),
            lambda: SendMessageRequest(chat_id=0, text="hi"),
            lambda: SendMessageRequest(chat_id=CHAT, text="x" * 4097),
            lambda: SendMessageRequest(chat_id=CHAT, text="😀" * 2049),
            lambda: SendMessageRequest(chat_id=CHAT, text="hi", parse_mode="HTML"),
            lambda: InlineKeyboardButton(text="a", callback_data="é" * 33),
            lambda: GetUpdatesRequest(allowed_updates=()),
        ]
        for build in bad:
            with self.assertRaises(ValidationError):
                build()

    async def test_credentials_redacted_and_invalid_configuration_is_safe(self):
        credentials = TelegramCredentials(token=TOKEN)
        self.assertNotIn(TOKEN, repr(credentials))
        self.assertNotIn(TOKEN, credentials.model_dump_json())
        client = self.client(
            lambda request: httpx.Response(200, json={"ok": True, "result": []})
        )
        self.assertNotIn(TOKEN, repr(client))
        with self.assertRaises(TelegramError) as caught:
            TelegramBotClient("bad secret")
        self.assertIsNone(caught.exception.__context__)
        self.assertNotIn("secret", str(caught.exception))
        with self.assertRaises(ValidationError):
            TelegramOptions(timeout_seconds=float("inf"))
        self.assertIsInstance(
            TelegramCredentials(token=SecretStr(TOKEN)), TelegramCredentials
        )

    async def test_timeout_and_malformed_receipts_unknown_without_retry(self):
        for response in [
            httpx.Response(503, json={"ok": False, "error_code": 503}),
            httpx.Response(
                302,
                headers={"location": "https://example.invalid"},
                json={"ok": True, "result": message()},
            ),
            httpx.Response(
                200,
                json={
                    "ok": True,
                    "result": message(chat={"id": 999, "type": "private"}),
                },
            ),
            httpx.Response(200, content=b"[" * 2000 + b"]" * 2000),
            httpx.Response(200, json={"ok": True, "result": {"message_id": True}}),
        ]:
            with self.subTest(status=response.status_code):
                calls = []

                def handle(request, response=response, calls=calls):
                    calls.append(request)
                    return response

                with self.assertRaises(TelegramError) as caught:
                    await self.client(handle).send_message(CHAT, "private")
                self.assertTrue(caught.exception.outcome_unknown)
                self.assertEqual(len(calls), 1)
                self.assertIsNone(caught.exception.__context__)

    async def test_network_error_does_not_retain_token_or_request(self):
        calls = []

        def handle(request):
            calls.append(request)
            raise httpx.ReadTimeout(TOKEN, request=request)

        with self.assertRaises(TelegramError) as caught:
            await self.client(handle).send_message(CHAT, "private")
        self.assertTrue(caught.exception.outcome_unknown)
        self.assertIsNone(caught.exception.__context__)
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertEqual(len(calls), 1)

    async def test_rate_limit_is_explicit_and_not_retried(self):
        calls = []

        def handle(request):
            calls.append(request)
            return httpx.Response(
                429,
                json={
                    "ok": False,
                    "error_code": 429,
                    "description": TOKEN,
                    "parameters": {"retry_after": 12},
                },
            )

        with self.assertRaises(TelegramError) as caught:
            await self.client(handle).send_message(CHAT, "private")
        self.assertFalse(caught.exception.outcome_unknown)
        self.assertEqual(caught.exception.retry_after_seconds, 12)
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertEqual(len(calls), 1)

    async def test_invalid_rows_never_return_a_partial_page(self):
        for result in [
            [{"update_id": 1, "message": message()}, {"update_id": "bad"}],
            [{"update_id": 2}, {"update_id": 1}],
            [{"update_id": 1}, {"update_id": 1}],
        ]:
            with self.subTest(result=result):
                client = self.client(
                    lambda request, result=result: httpx.Response(
                        200, json={"ok": True, "result": result}
                    )
                )
                with self.assertRaises(TelegramError):
                    await client.get_updates()

    async def test_offset_failure_marks_acknowledgement_uncertain(self):
        def handle(request):
            raise httpx.ReadTimeout(TOKEN, request=request)

        client = self.client(handle)
        with self.assertRaises(TelegramError) as caught:
            await client.get_updates(offset=12)
        self.assertTrue(caught.exception.outcome_unknown)

    async def test_limit_deadline_and_response_cap(self):
        client = self.client(
            lambda request: self.fail("Do not dispatch invalid deadline")
        )
        with self.assertRaises(TelegramError):
            await client.get_updates(timeout=30)
        client = self.client(
            lambda request: httpx.Response(200, content=b"x" * 2048),
            options=TelegramOptions(max_response_bytes=1024),
        )
        with self.assertRaises(TelegramError):
            await client.get_updates()
        ticks = iter([0.0, 40.0, 40.0])
        client = self.client(
            lambda request: httpx.Response(200, json={"ok": True, "result": []}),
            clock=lambda: next(ticks),
        )
        with self.assertRaises(TelegramError):
            await client.get_updates()

    async def test_ambient_proxy_environment_is_ignored(self):
        from unittest.mock import patch

        with patch.dict("os.environ", {"HTTPS_PROXY": "http://invalid.example:1"}):
            client = self.client(
                lambda request: httpx.Response(200, json={"ok": True, "result": []})
            )
            self.assertFalse(client._http.trust_env)
            self.assertEqual(await client.get_updates(), ())

    async def test_hosted_namespace_remains_available(self):
        from zeo_integrations.telegram import TelegramClient as HostedClient

        self.assertIsNot(HostedClient, TelegramBotClient)

    async def test_nontext_and_unsupported_payloads_are_preserved(self):
        picture = message()
        picture.pop("text")
        picture["photo"] = [{"file_id": "inert", "width": 12, "height": 12}]
        payloads = [
            {"update_id": 1, "message": picture},
            {"update_id": 2, "edited_message": message()},
        ]
        client = self.client(
            lambda request: httpx.Response(200, json={"ok": True, "result": payloads})
        )
        rows = await client.get_updates()
        self.assertIsNone(rows[0].message.text)
        self.assertEqual(rows[0].raw_payload, payloads[0])
        self.assertEqual(rows[1].raw_payload, payloads[1])
        self.assertEqual(rows[1].kind, "unsupported")

    async def test_context_manager_and_private_http_logging(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        logger = logging.getLogger("httpx")
        old_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            async with self.client(
                lambda request: httpx.Response(200, json={"ok": True, "result": []})
            ) as client:
                self.assertEqual(await client.get_updates(), ())
            self.assertTrue(client._http.is_closed)
            logger.info("unrelated public request")
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)
        self.assertNotIn(TOKEN, output.getvalue())
        self.assertIn("unrelated public request", output.getvalue())

    async def test_cancelled_send_is_uncertain_and_not_retried(self):
        dispatched = asyncio.Event()
        calls = []

        async def handle(request):
            calls.append(request)
            dispatched.set()
            await asyncio.Event().wait()

        client = self.client(handle)
        task = asyncio.create_task(client.send_message(CHAT, "hello"))
        await dispatched.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError) as caught:
            await task
        self.assertTrue(task.cancelled())
        self.assertIs(type(caught.exception), asyncio.CancelledError)
        self.assertEqual(str(caught.exception), "request_cancelled")
        self.assertIn("outcome_unknown=true", caught.exception.__notes__)
        self.assertIsNone(caught.exception.__context__)
        self.assertEqual(len(calls), 1)

    async def test_ambiguous_json_receipts_are_not_accepted(self):
        for body in [
            b'{"ok":true,"ok":false,"result":true}',
            b'{"ok":true,"result":NaN}',
        ]:
            client = self.client(
                lambda request, body=body: httpx.Response(200, content=body)
            )
            with self.assertRaises(TelegramError) as caught:
                await client.answer_callback_query("opaque")
            self.assertTrue(caught.exception.outcome_unknown)
            self.assertIsNone(caught.exception.__context__)

    async def test_malformed_message_preserves_page_for_explicit_quarantine(self):
        result = [
            {"update_id": 1, "message": message(date="bad")},
            {"update_id": 2, "message": message()},
        ]
        client = self.client(
            lambda request: httpx.Response(200, json={"ok": True, "result": result})
        )
        rows = await client.get_updates()
        self.assertEqual([row.update_id for row in rows], [1, 2])
        self.assertEqual(rows[0].kind, "unsupported")
        self.assertEqual(rows[0].unsupported_reason, "invalid_message")
        self.assertEqual(rows[0].raw_payload, result[0])
        self.assertEqual(rows[1].message.message_id, 5)

    async def test_taskgroup_cancellation_remains_cancellation(self):
        dispatched = asyncio.Event()

        async def handle(request):
            dispatched.set()
            await asyncio.Event().wait()

        client = self.client(handle)
        with self.assertRaises(ExceptionGroup):
            async with asyncio.TaskGroup() as group:
                task = group.create_task(client.send_message(CHAT, "hello"))
                await dispatched.wait()
                raise RuntimeError("fixture stops group")
        self.assertTrue(task.cancelled())

    async def test_outer_timeout_keeps_timeout_semantics(self):
        async def handle(request):
            await asyncio.Event().wait()

        client = self.client(handle)
        with self.assertRaises(TimeoutError):
            async with asyncio.timeout(0.01):
                await client.send_message(CHAT, "hello")

    async def test_bad_callback_and_conflicting_kinds_are_opaque(self):
        cases = [
            ({"callback_query": {"id": "missing-fields"}}, "invalid_callback_query"),
            (
                {"message": message(), "callback_query": {"id": "bad"}},
                "conflicting_kinds",
            ),
        ]
        for content, reason in cases:
            payload = {
                "update_id": 7,
                **content,
                "unsupported_reason": "untrusted-provider-field",
            }
            client = self.client(
                lambda request, payload=payload: httpx.Response(
                    200, json={"ok": True, "result": [payload]}
                )
            )
            rows = await client.get_updates()
            self.assertEqual(rows[0].kind, "unsupported")
            self.assertEqual(rows[0].unsupported_reason, reason)
            self.assertEqual(rows[0].raw_payload, payload)
            self.assertIsNone(rows[0].message)
            self.assertIsNone(rows[0].callback_query)
