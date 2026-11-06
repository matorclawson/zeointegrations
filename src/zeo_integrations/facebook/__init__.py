"""Bounded facebook operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import FacebookClient


class Client(BaseClient):
    provider = "facebook"
    implementation = FacebookClient
    origins = ("https://facebook-scraper3.p.rapidapi.com", "https://www.facebook.com")
    operations = (
        "search_locations",
        "get_page_details",
        "get_page_id",
        "get_post_comments",
        "get_post_details",
        "get_group_posts",
        "get_group_details",
        "get_group_id",
        "get_profile_posts",
        "get_profile_details_id",
        "get_profile_details_url",
        "get_profile_id",
        "get_me",
    )
