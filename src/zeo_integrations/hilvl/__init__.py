"""Bounded hilvl operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import HilvlClient


class Client(BaseClient):
    provider = "hilvl"
    implementation = HilvlClient
    origins = ("https://services.leadconnectorhq.com",)
    operations = (
        "get_business",
        "get_businesses_by_location",
        "create_business",
        "update_business",
        "delete_business",
        "get_calendars",
        "get_calendar",
        "create_calendar",
        "update_calendar",
        "delete_calendar",
        "get_free_slots",
        "create_block_slot",
        "get_contact",
        "create_contact",
        "update_contact",
        "delete_contact",
        "upsert_contact",
        "get_contacts_by_business",
        "get_tasks",
        "get_task",
        "create_task",
        "update_task",
        "delete_task",
        "update_task_completed",
        "get_appointments",
        "add_tags",
        "remove_tags",
        "get_notes",
        "get_note",
        "create_note",
        "update_note",
        "delete_note",
        "add_contact_to_campaign",
        "remove_contact_from_campaign",
        "remove_contact_from_all_campaigns",
        "add_contact_to_workflow",
        "remove_contact_from_workflow",
        "update_contacts_tags",
        "update_contacts_business",
        "get_duplicate_contact",
        "add_followers",
        "remove_followers",
        "get_conversation",
        "update_conversation",
        "delete_conversation",
        "create_conversation",
        "get_message_by_id",
        "get_email_by_id",
        "cancel_scheduled_email",
        "get_messages_by_conversation_id",
        "send_message",
    )
