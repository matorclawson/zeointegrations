# Direct Telegram Bot API transport

`zeo_integrations.telegram.direct.TelegramClient` is an async transport in the
single `zeo-integrations` distribution. It uses HTTPX and Pydantic v2, already
included in the base dependencies, and supports Python 3.12 and later.
The existing credentialless hosted `zeo_integrations.telegram.TelegramClient`
and `TelegramSender` retain their existing contracts.

Install the repository root at an exact reviewed commit, replacing `COMMIT`
with its full SHA:

```sh
pip install 'zeo-integrations @ git+https://github.com/zeroemployeeorg/zeointegrations.git@COMMIT'
```

The host supplies the token in memory and owns consent, chat admission, durable
update disposition, and business authorization. This library reads no credential
files or environment variables and starts no polling loop. Never print the token,
HTTP request URL, raw responses, or personal message content.

```python
from zeo_integrations.telegram.direct import TelegramClient

async def poll_one_page(injected_token: str, persisted_offset: int | None):
    async with TelegramClient(injected_token) as client:
        return await client.get_updates(
            offset=persisted_offset,
            limit=100,
            timeout=20,
            allowed_updates=("message", "callback_query"),
        )
```

`get_updates` returns an ordered tuple of typed `Update` models. Each has an
`update_id`, optional `message` or `callback_query`, and `kind`. Message fields
include `message_id`, Unix `date`, `chat.id`, `chat.type`, optional `text`, and
optional `from_user` (the native `from` field). Callback fields include `id`,
`data`, `from_user`, and optional `message`. Non-text messages and unsupported
updates retain their complete bounded JSON row in `raw_payload`; they must be
explicitly handled or durably quarantined, never silently skipped. Treat all
provider payloads and callback data as untrusted input.

The keyword-only `allowed_updates` accepts a nonempty, unique tuple containing
`"message"`, `"callback_query"`, or both. The default remains
`("message", "callback_query")`. Every poll sends the selected types explicitly;
it never relies on Telegram's remembered selection. Lists, empty tuples,
duplicates, and unsupported names fail with `invalid_request` before transport.
The example keeps callback delivery enabled. Receiving a callback does not grant
admin rights or business authorization. Previously queued other update types may
still arrive. A message or callback that cannot be
typed is returned as an `unsupported`
row with a fixed `unsupported_reason`, its strictly validated `update_id`,
and the complete `raw_payload`. Persist it in a restricted quarantine before
confirming past it; alert the operator rather than treating malformed content
as a business instruction. Other rows in the page remain available. Invalid
JSON, invalid/missing IDs, duplicate or out-of-order IDs, and oversized pages
still fail as a whole: no safe confirmation boundary is available. Pause and
escalate these failures; never advance the offset by guessing an ID. The client
never stores or advances offsets. Passing an offset confirms earlier updates
at Telegram, so persist the complete preceding page and its disposition before
advancing. A failed offset-bearing call may still have confirmed earlier updates.

`send_message(chat_id, text, reply_markup=None)` returns a typed `Message` with
Telegram's actual message ID, date, and matching destination chat. It sends plain
text only, with at most 4,096 UTF-16 units. Optional `InlineKeyboardMarkup` and
`InlineKeyboardButton` models live in `direct_models`; callback data is limited
to 64 UTF-8 bytes. `answer_callback_query(callback_query_id, text=None)` returns
`True` only for an acknowledged callback. It does not authorize a business action.

All three calls use a fixed HTTPS origin and one request, with no redirects,
ambient proxies, automatic sends, or retries. Default polling timeout is 20
seconds within a 35-second total deadline; polling may be configured up to 30
seconds when the total deadline leaves more than five seconds of margin.
Responses have a default 1 MiB cap, configurable up to 4 MiB through
`TelegramOptions`. The host owns the async client's lifecycle, preferably through
`async with`.

`TelegramError` exposes a fixed `code`, `outcome_unknown`, and optional
`retry_after_seconds`, with no provider description or raw HTTP exception attached.
A transport failure, timeout or malformed send receipt has an unknown outcome:
do not blindly retry the send. External cancellation propagates as the standard
`asyncio.CancelledError` with safe text and an `outcome_unknown=true` note for
writes or offset confirmations. It is not an ordinary `TelegramError`: allow
cancellation to stop the polling/controller task. TaskGroup cancellation and
an outer `asyncio.timeout` retain their standard behavior, including on Python
3.12. A canceled or timed-out write may have completed; never automatically
retry it. The API has no caller-supplied idempotency key for these sends. Explicit native 4xx refusals
are distinguished from uncertain outcomes. Rate-limit hints never trigger a retry.
A successful send is API acceptance, not proof of customer delivery or consent.
Caller-injected transports must preserve these no-retry and no-URL-logging rules.

The protocol reference is the official [Telegram Bot API](https://core.telegram.org/bots/api)
for `getUpdates`, `sendMessage`, and `answerCallbackQuery`. Verification uses only
inert credentials and offline HTTP doubles; it makes no live bot calls.
