"""Shared Telegram receive/ACK slice; hosted credential custody stays in Connect."""

from .client import TelegramClient
from .models import (
    DurablePrefixVerifier,
    TelegramAcknowledgement,
    TelegramBatch,
    TelegramCondition,
    TelegramError,
    TelegramRetention,
    TelegramUpdate,
)

__all__ = [
    "DurablePrefixVerifier",
    "TelegramAcknowledgement",
    "TelegramBatch",
    "TelegramClient",
    "TelegramCondition",
    "TelegramError",
    "TelegramRetention",
    "TelegramUpdate",
]
