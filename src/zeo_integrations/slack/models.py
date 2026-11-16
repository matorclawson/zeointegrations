"""Typed inputs and a deliberately limited conversation projection."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ConversationType = Literal["public_channel", "private_channel", "mpim", "im"]
Cursor = Annotated[str, Field(max_length=4096)]


class ConversationListRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    limit: int = Field(default=100, ge=1, le=200)
    cursor: Annotated[str, Field(min_length=1, max_length=4096)] | None = None
    types: list[ConversationType] = Field(
        default_factory=lambda: ["public_channel"], min_length=1, max_length=4
    )
    exclude_archived: bool = False
    team_id: Annotated[str, Field(min_length=1, max_length=128)] | None = None

    @field_validator("types")
    @classmethod
    def unique_types(cls, value: list[ConversationType]) -> list[ConversationType]:
        if len(set(value)) != len(value):
            raise ValueError("Conversation types must be unique")
        return value


class Conversation(BaseModel):
    """Projection only; missing classification facts stay unknown, never false."""

    model_config = ConfigDict(strict=True, extra="ignore", hide_input_in_errors=True)

    id: str = Field(min_length=1, max_length=256)
    name: str | None = Field(default=None, max_length=512)
    is_private: bool | None = None
    is_archived: bool | None = None
    is_channel: bool | None = None
    is_group: bool | None = None
    is_im: bool | None = None
    is_mpim: bool | None = None


class ConversationPage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    conversations: list[Conversation] = Field(max_length=200)
    next_cursor: Cursor | None = None
