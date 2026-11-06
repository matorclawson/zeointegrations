"""Bounded reads on one Connect-owned WhatsApp bridge identity. MIT.

No session enumeration, authentication, QR rendering or destructive disconnect.
The injected bridge implements VeyraX's read functions without logging messages
and must enforce deadlines and response limits before returning JSON data.
"""

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError
from zeo_integrations._http.runtime import _bounded


class Chats(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    query: str | None = Field(default=None, max_length=1024)
    limit: int = Field(default=20, ge=1, le=100)
    page: int = Field(default=0, ge=0, le=10000)
    include_last_message: bool = False


class Messages(Chats):
    chat_jid: str = Field(min_length=1, max_length=256)
    include_context: bool = False


class Chat(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    chat_jid: str = Field(min_length=1, max_length=256)
    include_last_message: bool = False


class Contacts(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    query: str = Field(min_length=1, max_length=1024)


class ReadClient:
    def __init__(self, bridge, *, user_id: str):
        if not isinstance(user_id, str) or not 1 <= len(user_id) <= 200:
            raise IntegrationError("BINDING")
        self.bridge, self.user_id = bridge, user_id

    def _read(self, call):
        failed = False
        try:
            result = call()
            _bounded(result, 1048576)
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("BRIDGE_READ_FAILED")
        return result

    def get_chats(self, query: Chats):
        query = Chats.model_validate(query.model_dump())
        return self._read(
            lambda: self.bridge.list_chats(
                self.user_id, **query.model_dump(), sort_by="last_active"
            )
        )

    def get_messages(self, query: Messages):
        query = Messages.model_validate(query.model_dump())
        return self._read(
            lambda: self.bridge.list_messages(
                self.user_id, **query.model_dump(exclude={"include_last_message"})
            )
        )

    def get_chat(self, query: Chat):
        query = Chat.model_validate(query.model_dump())
        return self._read(
            lambda: self.bridge.get_chat(self.user_id, **query.model_dump())
        )

    def get_contacts(self, query: Contacts):
        query = Contacts.model_validate(query.model_dump())
        return self._read(
            lambda: self.bridge.search_contacts(self.user_id, query.query)
        )
