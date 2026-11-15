"""Three fixed-origin Bot API calls. No environment/files, logging, or retries."""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from contextvars import ContextVar

import httpx
from pydantic import SecretStr, TypeAdapter, ValidationError

from .direct_models import (
    AnswerCallbackQueryRequest,
    ApiEnvelope,
    GetUpdatesRequest,
    InlineKeyboardMarkup,
    Message,
    RequestModel,
    SendMessageRequest,
    TelegramCredentials,
    TelegramOptions,
    Update,
)

_private_request: ContextVar[bool] = ContextVar(
    "telegram_direct_private_request", default=False
)


class _PrivateLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _private_request.get()


_private_filter = _PrivateLogs()


def _protect_logs() -> None:
    # Standard HTTP logs include the token-bearing URL. Suppress only this
    # async context, preserving concurrent unrelated caller logging.
    for name in (
        "httpx",
        "httpcore.connection",
        "httpcore.connection_pool",
        "httpcore.http11",
        "httpcore.http2",
        "httpcore.proxy",
        "httpcore.socks",
    ):
        logging.getLogger(name).addFilter(_private_filter)


class TelegramError(RuntimeError):
    """Fixed safe text only. UNKNOWN effects require caller reconciliation."""

    def __init__(
        self,
        code: str,
        *,
        outcome_unknown: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.code = code
        self.outcome_unknown = outcome_unknown
        self.retry_after_seconds = retry_after_seconds
        super().__init__(code)


def _request[T: RequestModel](model: type[T], **values: object) -> T:
    validated = None
    try:
        validated = model.model_validate(values)
    except (ValueError, TypeError, RecursionError):
        pass
    if validated is None:
        raise TelegramError("invalid_request")
    return validated


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> object:
    raise ValueError("Nonfinite JSON constant")


class TelegramClient:
    """Async client with explicit credentials and owned HTTP lifecycle.

    Inject a token at construction. The client owns its HTTP session; injected
    transports are for controlled hosting/tests and must not retry or log URLs.
    Neither this object nor its errors retain raw provider exception objects.
    """

    def __init__(
        self,
        token: str | SecretStr,
        *,
        options: TelegramOptions | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        invalid = False
        try:
            self._credentials = TelegramCredentials(token=token)
            self._options = TelegramOptions.model_validate(
                options.model_dump() if options is not None else {}
            )
        except (ValidationError, ValueError, TypeError, AttributeError):
            invalid = True
        if invalid:
            raise TelegramError("invalid_configuration")
        _protect_logs()
        self._clock = clock
        self._http = httpx.AsyncClient(
            transport=transport,
            trust_env=False,
            follow_redirects=False,
            timeout=self._options.timeout_seconds,
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )

    def __repr__(self) -> str:
        return "TelegramClient(<redacted>)"

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "TelegramClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def _call(
        self, method: str, request: RequestModel, *, effect: bool
    ) -> object:
        # Closed call sites only; there is no public arbitrary URL/method API.
        if method not in {"getUpdates", "sendMessage", "answerCallbackQuery"}:
            raise TelegramError("unsupported_method")
        payload = request.model_dump(mode="json", exclude_none=True)
        token = self._credentials.token.get_secret_value()
        failed = False
        status = 0
        raw = bytearray()
        started = self._clock()
        cancelled = False
        context_token = _private_request.set(True)
        try:
            async with asyncio.timeout(self._options.timeout_seconds):
                async with self._http.stream(
                    "POST",
                    f"https://api.telegram.org/bot{token}/{method}",
                    json=payload,
                ) as response:
                    status = response.status_code
                    if response.headers.get(
                        "content-encoding", "identity"
                    ).lower() not in {
                        "identity",
                        "",
                    }:
                        raise ValueError("encoded response")
                    async for chunk in response.aiter_bytes():
                        if self._clock() - started >= self._options.timeout_seconds:
                            raise ValueError("deadline")
                        if len(raw) + len(chunk) > self._options.max_response_bytes:
                            raise ValueError("response limit")
                        raw.extend(chunk)
                    if self._clock() - started >= self._options.timeout_seconds:
                        raise ValueError("deadline")
        except asyncio.CancelledError:
            cancelled = True
        except Exception:
            failed = True
        finally:
            _private_request.reset(context_token)
        # Raise outside the handler so neither __context__ nor a raw HTTP URL
        # with its token is attached to the safe public exception.
        if cancelled:
            raise TelegramError("request_cancelled", outcome_unknown=effect)
        if failed:
            raise TelegramError("transport_unavailable", outcome_unknown=effect)
        envelope = None
        try:
            envelope = ApiEnvelope.model_validate(
                json.loads(
                    raw,
                    object_pairs_hook=_unique_object,
                    parse_constant=_invalid_constant,
                )
            )
        except (ValueError, TypeError, UnicodeError, RecursionError):
            pass
        if envelope is None:
            raise TelegramError("invalid_response", outcome_unknown=effect)
        if not envelope.ok:
            code = envelope.error_code
            if (
                code is not None
                and 400 <= code < 500
                and code != 408
                and (status == 200 or status == code)
            ):
                retry = envelope.parameters.retry_after if envelope.parameters else None
                raise TelegramError("provider_refused", retry_after_seconds=retry)
            raise TelegramError("provider_unavailable", outcome_unknown=effect)
        if status != 200 or envelope.error_code is not None:
            raise TelegramError("invalid_response", outcome_unknown=effect)
        return envelope.result

    async def get_updates(
        self,
        offset: int | None = None,
        *,
        limit: int = 100,
        timeout: int = 20,
    ) -> tuple[Update, ...]:
        """One page only. A passed offset confirms all earlier provider updates.

        Persist and process the complete previous page before advancing offset.
        This call never chooses, persists, or advances the offset on your behalf.
        A failed call cannot prove whether an explicitly passed offset took effect.
        """
        request = _request(
            GetUpdatesRequest, offset=offset, limit=limit, timeout=timeout
        )
        if request.timeout + 5 >= self._options.timeout_seconds:
            raise TelegramError("poll_timeout_exceeds_deadline")
        effect = request.offset is not None
        result = await self._call("getUpdates", request, effect=effect)
        updates = None
        try:
            updates = TypeAdapter(tuple[Update, ...]).validate_python(
                tuple(result) if isinstance(result, list) else result, strict=True
            )
        except (ValidationError, TypeError, ValueError, RecursionError):
            pass
        if updates is None or len(updates) > request.limit:
            raise TelegramError("invalid_updates", outcome_unknown=effect)
        ids = [row.update_id for row in updates]
        if ids != sorted(set(ids)) or (
            request.offset is not None and any(i < request.offset for i in ids)
        ):
            raise TelegramError("invalid_update_order", outcome_unknown=effect)
        return updates

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        """A valid response means API acceptance, not customer delivery/consent."""
        request = _request(
            SendMessageRequest, chat_id=chat_id, text=text, reply_markup=reply_markup
        )
        result = await self._call("sendMessage", request, effect=True)
        message = None
        try:
            message = Message.model_validate(result)
        except (ValidationError, TypeError, ValueError, RecursionError):
            pass
        if (
            message is None
            or message.chat.id != request.chat_id
            or message.message_id <= 0
            or message.date <= 0
        ):
            raise TelegramError("invalid_send_receipt", outcome_unknown=True)
        return message

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        *,
        show_alert: bool = False,
        cache_time: int = 0,
    ) -> bool:
        """Acknowledge callback UI only, never authorize a business action."""
        request = _request(
            AnswerCallbackQueryRequest,
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            cache_time=cache_time,
        )
        result = await self._call("answerCallbackQuery", request, effect=True)
        if result is not True:
            raise TelegramError("invalid_callback_receipt", outcome_unknown=True)
        return True
