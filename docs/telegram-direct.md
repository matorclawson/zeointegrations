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
        return await client.get_updates(offset=persisted_offset, limit=100, timeout=20)
```

`get_updates` returns an ordered tuple of typed `Update` models. Each has an
`update_id`, optional `message` or `callback_query`, and `kind`. Message fields
include `message_id`, Unix `date`, `chat.id`, `chat.type`, optional `text`, and
optional `from_user` (the native `from` field). Callback fields include `id`,
`data`, `from_user`, and optional `message`. Non-text messages and unsupported
updates retain their complete bounded JSON row in `raw_payload`; they must be
explicitly handled or durably quarantined, never silently skipped. Treat all
provider payloads and callback data as untrusted input.

The request subscribes to messages and callback queries. Previously queued
other update types may still arrive. A response that cannot be validated fails
as a whole; no partial page or implicit acknowledgement is returned. The client
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
A transport failure, timeout, malformed send receipt, or cancellation after a
write starts has an unknown outcome: do not blindly retry the send. The API has
no caller-supplied idempotency key for these sends. Explicit native 4xx refusals
are distinguished from uncertain outcomes. Rate-limit hints never trigger a retry.
A successful send is API acceptance, not proof of customer delivery or consent.
Caller-injected transports must preserve these no-retry and no-URL-logging rules.

The protocol reference is the official [Telegram Bot API](https://core.telegram.org/bots/api)
for `getUpdates`, `sendMessage`, and `answerCallbackQuery`. Verification uses only
inert credentials and offline HTTP doubles; it makes no live bot calls.
