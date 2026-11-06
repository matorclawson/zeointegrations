"""Bounded cal operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import CalClient


class Client(BaseClient):
    provider = "cal"
    implementation = CalClient
    origins = ("https://api.cal.com",)
    operations = (
        "get_bookings",
        "get_booking",
        "create_booking",
        "reschedule_booking",
        "cancel_booking",
        "get_me",
        "get_schedules",
        "get_schedule",
        "update_schedule",
        "get_event_types",
    )
