"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/cal/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class CalClient:
    BASE_URL = "https://api.cal.com/v2"
    BOOKINGS_API_VERSION = "2024-08-13"
    EVENT_TYPES_API_VERSION = "2024-06-14"
    SCHEDULES_API_VERSION = "2024-06-11"

    def __init__(self, transport):
        self._http = transport
        self.default_headers = {"Content-Type": "application/json"}

    def _get_headers(self, api_version: str) -> dict[str, str]:
        headers = self.default_headers.copy()
        headers["cal-api-version"] = api_version
        return headers

    def get_bookings(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/bookings",
            headers=self._get_headers(self.BOOKINGS_API_VERSION),
            params=self._clean_params(params),
        )
        response.raise_for_status()
        return response.json()

    def get_booking(self, booking_uid: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/bookings/{booking_uid}",
            headers=self._get_headers(self.BOOKINGS_API_VERSION),
        )
        response.raise_for_status()
        return response.json()

    def create_booking(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/bookings",
            headers=self._get_headers(self.BOOKINGS_API_VERSION),
            json=params,
        )
        response.raise_for_status()
        return response.json()

    def reschedule_booking(
        self, booking_uid: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/bookings/{booking_uid}/reschedule",
            headers=self._get_headers(self.BOOKINGS_API_VERSION),
            json=params,
        )
        response.raise_for_status()
        return response.json()

    def cancel_booking(
        self, booking_uid: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.post(
            f"{self.BASE_URL}/bookings/{booking_uid}/cancel",
            headers=self._get_headers(self.BOOKINGS_API_VERSION),
            json=params,
        )
        response.raise_for_status()
        return response.json()

    def get_me(self) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/me", headers=self._get_headers(self.BOOKINGS_API_VERSION)
        )
        response.raise_for_status()
        return response.json()

    def get_schedules(self) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/schedules",
            headers=self._get_headers(self.SCHEDULES_API_VERSION),
        )
        response.raise_for_status()
        return response.json()

    def get_schedule(self, schedule_id: int) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/schedules/{schedule_id}",
            headers=self._get_headers(self.SCHEDULES_API_VERSION),
        )
        response.raise_for_status()
        return response.json()

    def update_schedule(
        self, schedule_id: int, params: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._http.patch(
            f"{self.BASE_URL}/schedules/{schedule_id}",
            headers=self._get_headers(self.SCHEDULES_API_VERSION),
            json=params,
        )
        response.raise_for_status()
        return response.json()

    def get_event_types(self, params: dict[str, Any]) -> dict[str, Any]:
        query_params = self._clean_params(params)
        response = self._http.get(
            f"{self.BASE_URL}/event-types",
            headers=self._get_headers(self.EVENT_TYPES_API_VERSION),
            params=query_params,
        )
        response.raise_for_status()
        return response.json()

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in params.items() if v is not None}
