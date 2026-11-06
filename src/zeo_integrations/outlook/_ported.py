"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/outlook/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class OutlookClient:
    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, transport):
        self._http = transport
        self.session = self._http
        self.session.headers.update({"Content-Type": "application/json"})

    def list_messages(self, **kwargs) -> dict[str, Any]:
        params = {k: v for k, v in kwargs.items() if v is not None}
        response = self.session.get(f"{self.BASE_URL}/me/messages", params=params)
        response.raise_for_status()
        return response.json()

    def get_message(self, message_id: str) -> dict[str, Any]:
        response = self.session.get(f"{self.BASE_URL}/me/messages/{message_id}")
        response.raise_for_status()
        return response.json()

    def create_draft(self, message: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(f"{self.BASE_URL}/me/messages", json=message)
        response.raise_for_status()
        return response.json()

    def delete_message(self, message_id: str) -> None:
        response = self.session.delete(f"{self.BASE_URL}/me/messages/{message_id}")
        response.raise_for_status()

    def send_message(self, message: dict[str, Any]) -> None:
        message_payload = {
            "message": {
                "subject": message.get("subject"),
                "body": message.get("body"),
                "toRecipients": message.get("toRecipients"),
            }
        }
        response = self.session.post(
            f"{self.BASE_URL}/me/sendMail", json=message_payload
        )
        response.raise_for_status()

    def update_message(
        self, message_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        response = self.session.patch(
            f"{self.BASE_URL}/me/messages/{message_id}", json=message
        )
        response.raise_for_status()
        return response.json()

    def list_calendars(self) -> dict[str, Any]:
        response = self.session.get(f"{self.BASE_URL}/me/calendars")
        response.raise_for_status()
        return response.json()

    def list_events(self, calendar_id: str = None, **kwargs) -> dict[str, Any]:
        if calendar_id:
            path = f"/me/calendars/{calendar_id}/events"
        else:
            path = "/me/calendar/events"
        params = {k: v for k, v in kwargs.items() if v is not None}
        response = self.session.get(f"{self.BASE_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()

    def get_event(self, event_id: str, calendar_id: str = None) -> dict[str, Any]:
        calendar_path = f"/calendars/{calendar_id}" if calendar_id else ""
        response = self.session.get(
            f"{self.BASE_URL}/me{calendar_path}/events/{event_id}"
        )
        response.raise_for_status()
        return response.json()

    def create_event(
        self, event: dict[str, Any], calendar_id: str = None
    ) -> dict[str, Any]:
        if calendar_id:
            path = f"/me/calendars/{calendar_id}/events"
        else:
            path = "/me/calendar/events"
        response = self.session.post(f"{self.BASE_URL}{path}", json=event)
        response.raise_for_status()
        return response.json()

    def update_event(
        self, event_id: str, event: dict[str, Any], calendar_id: str = None
    ) -> dict[str, Any]:
        if calendar_id:
            path = f"/me/calendars/{calendar_id}/events/{event_id}"
        else:
            path = f"/me/calendar/events/{event_id}"
        response = self.session.patch(f"{self.BASE_URL}{path}", json=event)
        response.raise_for_status()
        return response.json()

    def delete_event(self, event_id: str, calendar_id: str = None) -> None:
        if calendar_id:
            path = f"/me/calendars/{calendar_id}/events/{event_id}"
        else:
            path = f"/me/calendar/events/{event_id}"
        response = self.session.delete(f"{self.BASE_URL}{path}")
        response.raise_for_status()
