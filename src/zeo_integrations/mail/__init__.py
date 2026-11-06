"""SMTP messages through an injected, already authenticated SMTP connection.

Copyright 2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
No login, environment lookup, session store, or automatic retry.
"""

from email.message import EmailMessage

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from zeo_integrations._http import IntegrationError


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    sender: EmailStr
    recipients: list[EmailStr] = Field(min_length=1, max_length=100)
    subject: str = Field(max_length=998)
    text: str = Field(max_length=100000)


class Client:
    def __init__(self, smtp):
        self.smtp = smtp

    def send(self, message: Message, *, allow_effect: bool = False):
        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        message = Message.model_validate(message.model_dump())
        if "\r" in message.subject or "\n" in message.subject:
            raise IntegrationError("HEADER")
        mail = EmailMessage()
        mail["From"], mail["To"] = message.sender, ", ".join(message.recipients)
        mail["Subject"] = message.subject
        mail.set_content(message.text)
        failed = False
        try:
            refused = self.smtp.send_message(
                mail, from_addr=message.sender, to_addrs=message.recipients
            )
            if not isinstance(refused, dict) or refused:
                failed = True
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("DELIVERY_UNCONFIRMED", outcome_unknown=True)
        return {"accepted_by_server": True, "delivered": None}
