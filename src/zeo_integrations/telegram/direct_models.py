"""Validated public Bot API boundaries; no provider credential discovery."""

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    SecretStr,
    field_validator,
    model_validator,
)

Id = Annotated[int, Field(ge=-(2**52), le=2**52)]
PositiveId = Annotated[int, Field(gt=0, le=2**52)]


class RequestModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        revalidate_instances="always",
    )


class ResponseModel(BaseModel):
    # Telegram adds fields. Preserve the explicit supported subset, never treat
    # unknown fields as authorization or forward them to a tool/model.
    model_config = ConfigDict(
        strict=True,
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
        revalidate_instances="always",
    )


class TelegramCredentials(RequestModel):
    token: SecretStr = Field(repr=False, exclude=True)

    @field_validator("token")
    @classmethod
    def valid_token(cls, token: SecretStr) -> SecretStr:
        import re

        if not re.fullmatch(
            r"[0-9]{1,16}:[A-Za-z0-9_-]{20,128}", token.get_secret_value()
        ):
            raise ValueError("Invalid bot token shape")
        return token


class TelegramOptions(RequestModel):
    timeout_seconds: Annotated[float, Field(gt=0, le=120, allow_inf_nan=False)] = 35.0
    max_response_bytes: Annotated[int, Field(ge=1024, le=4_194_304)] = 1_048_576


class User(ResponseModel):
    id: PositiveId = Field(repr=False)
    is_bot: bool
    first_name: str = Field(repr=False, max_length=1024)
    username: str | None = Field(default=None, repr=False, max_length=1024)


class Chat(ResponseModel):
    id: Id = Field(repr=False)
    type: Literal["private", "group", "supergroup", "channel"]

    @field_validator("id")
    @classmethod
    def nonzero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Chat id cannot be zero")
        return value


class Message(ResponseModel):
    message_id: Annotated[int, Field(ge=0)]
    date: Annotated[int, Field(ge=0)]
    chat: Chat = Field(repr=False)
    from_user: User | None = Field(default=None, alias="from", repr=False)
    text: str | None = Field(default=None, repr=False, max_length=16384)


class CallbackQuery(ResponseModel):
    id: str = Field(min_length=1, max_length=256, repr=False)
    from_user: User = Field(alias="from", repr=False)
    chat_instance: str = Field(min_length=1, max_length=256, repr=False)
    message: Message | None = Field(default=None, repr=False)
    inline_message_id: str | None = Field(default=None, repr=False)
    data: str | None = Field(default=None, repr=False, max_length=256)


class Update(ResponseModel):
    # Preserve every bounded provider field for durable caller disposition,
    # including unsupported update kinds and non-text messages. Never authorize
    # a business action from these untrusted values without caller admission.
    raw_payload: dict[str, JsonValue] = Field(default_factory=dict, repr=False)

    @model_validator(mode="before")
    @classmethod
    def preserve_payload(cls, value):
        if isinstance(value, dict):
            return {
                **value,
                "raw_payload": {k: v for k, v in value.items() if k != "raw_payload"},
            }
        return value

    update_id: Annotated[int, Field(ge=0, le=2**53)]
    message: Message | None = Field(default=None, repr=False)
    callback_query: CallbackQuery | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def single_kind(self) -> "Update":
        if self.message is not None and self.callback_query is not None:
            raise ValueError("Conflicting update kinds")
        return self

    @property
    def kind(self) -> Literal["message", "callback_query", "unsupported"]:
        if self.message is not None:
            return "message"
        if self.callback_query is not None:
            return "callback_query"
        return "unsupported"


class GetUpdatesRequest(RequestModel):
    # Non-negative offsets only: negative offsets discard history.
    offset: Annotated[int, Field(ge=0, le=2**53)] | None = None
    limit: Annotated[int, Field(ge=1, le=100)] = 100
    timeout: Annotated[int, Field(ge=0, le=30)] = 20
    allowed_updates: tuple[Literal["message", "callback_query"], ...] = (
        "message",
        "callback_query",
    )

    @field_validator("allowed_updates")
    @classmethod
    def supported(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or len(value) != len(set(value)):
            raise ValueError("Choose unique supported update types")
        return value


class InlineKeyboardButton(RequestModel):
    text: str = Field(min_length=1, max_length=128, repr=False)
    callback_data: str = Field(min_length=1, max_length=64, repr=False)

    @field_validator("callback_data")
    @classmethod
    def bounded_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 64:
            raise ValueError("Callback data exceeds 64 bytes")
        return value


class InlineKeyboardMarkup(RequestModel):
    inline_keyboard: tuple[tuple[InlineKeyboardButton, ...], ...] = Field(
        min_length=1, max_length=8, repr=False
    )

    @field_validator("inline_keyboard")
    @classmethod
    def bounded_rows(cls, rows: tuple[tuple[InlineKeyboardButton, ...], ...]):
        if any(not 1 <= len(row) <= 8 for row in rows):
            raise ValueError("Keyboard rows must contain 1 to 8 buttons")
        return rows


class SendMessageRequest(RequestModel):
    chat_id: Id = Field(repr=False)
    text: str = Field(min_length=1, max_length=4096, repr=False)
    reply_markup: InlineKeyboardMarkup | None = Field(default=None, repr=False)

    @field_validator("chat_id")
    @classmethod
    def nonzero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Chat id cannot be zero")
        return value

    @field_validator("text")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        if len(value.encode("utf-16-le")) // 2 > 4096:
            raise ValueError("Message exceeds 4096 UTF-16 units")
        return value


class AnswerCallbackQueryRequest(RequestModel):
    callback_query_id: str = Field(min_length=1, max_length=256, repr=False)
    text: str | None = Field(default=None, max_length=200, repr=False)
    show_alert: bool = False
    cache_time: Annotated[int, Field(ge=0, le=3600)] = 0


class ResponseParameters(ResponseModel):
    retry_after: Annotated[int, Field(ge=0, le=86400)] | None = None


class ApiEnvelope(ResponseModel):
    ok: bool
    result: object = Field(default=None, repr=False)
    error_code: Annotated[int, Field(ge=100, le=599)] | None = None
    parameters: ResponseParameters | None = None
