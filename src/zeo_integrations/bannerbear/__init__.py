"""Bounded bannerbear operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import BannerbearClient


class Client(BaseClient):
    provider = "bannerbear"
    implementation = BannerbearClient
    origins = ("https://api.bannerbear.com",)
    operations = (
        "retrieve_account_status",
        "create_image",
        "retrieve_image",
        "list_all_images",
        "create_video",
        "retrieve_video",
        "update_video",
        "list_all_videos",
        "create_collection",
        "retrieve_collection",
        "list_all_collections",
        "create_animated_gif",
        "retrieve_animated_gif",
        "list_all_animated_gifs",
        "create_screenshot",
        "retrieve_screenshot",
        "list_all_screenshots",
        "create_template",
        "duplicate_template",
        "retrieve_template",
        "update_template",
        "list_all_templates",
        "import_templates",
        "create_template_set",
        "update_template_set",
        "retrieve_template_set",
        "list_all_template_sets",
        "create_video_template",
        "retrieve_video_template",
        "list_all_video_templates",
        "create_session",
        "retrieve_session",
        "list_all_sessions",
        "create_webhook",
        "retrieve_webhook",
        "delete_webhook",
        "create_movie",
        "retrieve_movie",
        "list_all_movies",
        "create_diagnosis",
        "retrieve_diagnosis",
        "create_signed_base",
        "list_signed_bases",
        "create_project",
        "retrieve_project",
        "hydrate_project",
        "list_all_projects",
        "list_fonts",
        "list_effects",
        "join_pdf",
        "retrieve_joined_pdf",
        "rasterize_pdf",
        "retrieve_rasterized_pdf",
    )
