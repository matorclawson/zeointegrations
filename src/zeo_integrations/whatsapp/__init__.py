"""WhatsApp send using an injected Connect-owned QR/session bridge. MIT.

The bridge callable follows VeyraX's send_message(user_id, recipient, message,
timeout) interface. No QR authentication, credential store or bridge daemon is
copied. A successfully accepted send is not proof of recipient delivery.
"""

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from zeo_integrations._http import IntegrationError


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    recipient: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=16000)
    timeout: int = Field(default=30, ge=1, le=60)


class Client:
    def __init__(self, sender: Callable, *, user_id: str):
        if not isinstance(user_id, str) or not 1 <= len(user_id) <= 200:
            raise IntegrationError("BINDING")
        self.sender, self.user_id = sender, user_id

    def send(self, message: Message, *, allow_effect: bool = False):
        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        message = Message.model_validate(message.model_dump())
        failed = False
        try:
            response = self.sender(
                self.user_id,
                message.recipient,
                message.message,
                timeout=message.timeout,
            )
            failed = not (
                isinstance(response, tuple)
                and len(response) == 2
                and response[0] is True
            )
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("DELIVERY_UNCONFIRMED", outcome_unknown=True)
        return {"accepted_by_bridge": True, "delivered": None}
