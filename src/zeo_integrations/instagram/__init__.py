"""Bounded instagram operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import InstagramClient


class Client(BaseClient):
    provider = "instagram"
    implementation = InstagramClient
    origins = ("https://instagram230.p.rapidapi.com",)
    operations = (
        "get_user_details",
        "get_me",
        "get_user_posts",
        "get_user_following",
        "get_user_followers",
        "get_post_details",
        "get_post_comments",
    )
