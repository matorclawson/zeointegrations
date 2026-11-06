"""Bounded heygen operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import HeygenClient


class Client(BaseClient):
    provider = "heygen"
    implementation = HeygenClient
    origins = ("https://api.heygen.com", "https://upload.heygen.com")
    operations = (
        "list_avatars",
        "list_voices",
        "list_avatar_groups",
        "list_group_avatars",
        "generate_video",
        "get_video_status",
        "delete_video",
        "generate_webm",
        "list_videos",
        "share_video",
        "list_templates",
        "get_template_details",
        "generate_from_template",
        "get_supported_languages",
        "translate_video",
        "get_translation_status",
        "get_translation_caption",
        "generate_photo_avatar",
        "get_generation_status",
        "add_motion",
        "add_sound_effect",
        "get_user_info",
        "get_remaining_quota",
        "list_folders",
        "create_folder",
    )
