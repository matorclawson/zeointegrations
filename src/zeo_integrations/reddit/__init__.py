"""Bounded reddit operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import RedditClient


class Client(BaseClient):
    provider = "reddit"
    implementation = RedditClient
    origins = ("https://oauth.reddit.com",)
    operations = (
        "get_subreddit_posts",
        "create_comment",
        "create_post",
        "get_comment",
        "delete_post",
        "delete_comment",
        "edit_post",
        "edit_comment",
        "search",
        "get_comments",
        "get_user_info",
        "vote_post",
        "vote_comment",
        "save_post",
        "save_comment",
        "unsave_post",
        "unsave_comment",
        "get_my_info",
        "get_my_subreddits",
        "get_link_flairs",
    )
