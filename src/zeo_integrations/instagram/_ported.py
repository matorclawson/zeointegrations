"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/instagram/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

import re
from typing import Any

from zeo_integrations._http.runtime import HTTPException


class InstagramClient:
    BASE_URL = "https://instagram230.p.rapidapi.com"

    def __init__(self, transport, username: str | None = None):
        self._http = transport
        self.username = self.parse_instagram_username(username) if username else None
        self.headers = {"x-rapidapi-host": "instagram230.p.rapidapi.com"}

    @staticmethod
    def parse_instagram_username(username_input: str) -> str:
        if not username_input:
            return ""
        instagram_format = re.match("^(.+)@instagram$", username_input)
        if instagram_format:
            return instagram_format.group(1)
        if username_input.startswith("@"):
            username_input = username_input[1:]
        instagram_url_pattern = (
            "(?:https?:\\/\\/)?(?:www\\.)?(?:instagram\\.com)\\/([a-zA-Z0-9_\\."
            "]+)(?:\\?.*)?$"
        )
        url_match = re.search(instagram_url_pattern, username_input)
        if url_match:
            return url_match.group(1)
        return username_input.strip()

    def get_user_details(self, username: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/user/details"
        response = self._http.get(
            url, headers=self.headers, params={"username": username}
        )
        response.raise_for_status()
        return response.json()

    def get_me(self) -> dict[str, Any]:
        if not self.username:
            raise HTTPException(
                status_code=405,
                detail="Username must be configured.",
            )
        return self.get_user_details(username=self.username)

    def get_user_posts(
        self, username: str, cursor: str | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/user/posts"
        params = {"username": username}
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_following(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/user/following"
        params = {"user_id": user_id, "count": count}
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_followers(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/user/followers"
        params = {"user_id": user_id, "count": count}
        if cursor:
            params["cursor"] = cursor
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_post_details(self, shortcode: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/post/details"
        params = {"shortcode": shortcode}
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_post_comments(
        self, pk: str, next_min_id: str | None = None
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/post/comments"
        params = {"pk": pk}
        if next_min_id:
            params["next_min_id"] = next_min_id
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
