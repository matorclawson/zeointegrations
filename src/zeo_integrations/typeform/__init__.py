"""Bounded typeform operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TypeformClient


class Client(BaseClient):
    provider = "typeform"
    implementation = TypeformClient
    origins = ("https://api.typeform.com",)
    operations = (
        "get_account_workspaces",
        "create_account_workspace",
        "get_workspaces",
        "create_workspace",
        "delete_workspace",
        "get_workspace",
        "update_workspace",
        "get_forms",
        "create_form",
        "delete_form",
        "get_form",
        "update_form_patch",
        "update_form",
        "get_form_messages",
        "update_form_messages",
        "get_translation_payload",
        "get_translation_statuses",
        "delete_form_translation",
        "get_form_translation",
        "update_form_translation",
        "auto_translate_form",
        "get_images",
        "delete_image",
        "get_image",
        "get_background_image",
        "get_choice_image",
        "get_image_by_size",
        "get_themes",
        "create_theme",
        "delete_theme",
        "get_theme",
        "update_theme_partial",
        "update_theme_full",
        "delete_responses",
        "get_responses",
        "download_form_files",
        "get_response_file",
        "get_form_insights",
        "get_webhooks",
        "get_webhook",
        "create_or_update_webhook",
        "delete_webhook",
    )
