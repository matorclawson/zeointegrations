"""MIT read-only port, VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df.
Source: aci_server/integrations/x/client.py. No publishing operation.
"""

import re
from typing import Any

from zeo_integrations._http.runtime import HTTPException


class TwitterClient:
    BASE_URL = "https://twitter-api45.p.rapidapi.com"

    def __init__(self, transport, username: str | None = None):
        self._http = transport
        self.username = self.parse_twitter_username(username) if username else None
        self.headers = {"x-rapidapi-host": "twitter-api45.p.rapidapi.com"}

    @staticmethod
    def parse_twitter_username(username_input: str) -> str:
        """
        Parse Twitter/X username from various formats:
        - @username
        - https://twitter.com/username
        - http://twitter.com/username
        - https://x.com/username
        - http://x.com/username
        - twitter.com/username
        - x.com/username
        - mobile.twitter.com/username
        - username

        Returns the clean username without @ or URL components.
        """
        if not username_input:
            return ""
        if username_input.startswith("@"):
            username_input = username_input[1:]
        twitter_url_pattern = "(?:https?:\\/\\/)?(?:www\\.|mobile\\.)?(?:twitter\\.com|x\\.com)\\/([a-zA-Z0-9_]+)(?:\\?.*)?$"  # noqa: E501
        url_match = re.search(twitter_url_pattern, username_input)
        if url_match:
            return url_match.group(1)
        return username_input.strip()

    def get_user_profile(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/screenname.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_me(self) -> dict[str, Any]:
        """Get the authenticated user's profile based on the stored username."""
        if not self.username:
            raise HTTPException(
                status_code=405,
                detail="Username must be configured.",
            )
        return self.get_user_profile({"screenname": self.username})

    def get_user_timeline(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/timeline.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_user_following(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/following.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_user_followers(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/followers.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_tweet(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/tweet.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_tweet_retweets(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/retweets.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def search_tweets(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/search.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_tweet_thread(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/tweet_thread.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_latest_replies(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/latest_replies.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_list_timeline(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/listtimeline.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_community_timeline(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/community_timeline.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_list_followers(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/list_followers.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_list_members(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/list_members.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()

    def get_space(self, parameters: dict) -> dict[str, Any]:
        url = f"{self.BASE_URL}/spaces.php"
        response = self._http.get(url, headers=self.headers, params=parameters)
        response.raise_for_status()
        return response.json()
