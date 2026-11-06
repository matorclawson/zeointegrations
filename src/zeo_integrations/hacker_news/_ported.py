"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/hacker_news/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any

from zeo_integrations._http import compatibility as requests


class HackerNewsClient:
    """Client for interacting with Hacker News API"""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, transport):
        self._http = transport
        pass

    def get_top_stories(self) -> list[int]:
        response = self._http.get(f"{self.BASE_URL}/topstories.json")
        response.raise_for_status()
        return response.json()

    def get_new_stories(self) -> list[int]:
        response = self._http.get(f"{self.BASE_URL}/newstories.json")
        response.raise_for_status()
        return response.json()

    def get_best_stories(self) -> list[int]:
        response = self._http.get(f"{self.BASE_URL}/beststories.json")
        response.raise_for_status()
        return response.json()

    def get_ask_stories(self) -> list[int]:
        response = self._http.get(f"{self.BASE_URL}/askstories.json")
        response.raise_for_status()
        return response.json()

    def get_show_stories(self) -> list[int]:
        """Get IDs of Show HN stories"""
        response = self._http.get(f"{self.BASE_URL}/showstories.json")
        response.raise_for_status()
        return response.json()

    def get_job_stories(self) -> list[int]:
        """Get IDs of job stories"""
        response = self._http.get(f"{self.BASE_URL}/jobstories.json")
        response.raise_for_status()
        return response.json()

    def get_item(self, item_id: int) -> dict[str, Any]:
        """Get details of a specific item (story, comment, etc.)"""
        response = self._http.get(f"{self.BASE_URL}/item/{item_id}.json")
        response.raise_for_status()
        return response.json()

    def get_user(self, username: str) -> dict[str, Any]:
        """Get details of a specific user"""
        response = self._http.get(f"{self.BASE_URL}/user/{username}.json")
        response.raise_for_status()
        return response.json()

    def get_items_batch(self, item_ids: list[int]) -> list[dict[str, Any]]:
        """Get details of multiple items in batch"""
        items = []
        for item_id in item_ids:
            try:
                item = self.get_item(item_id)
                if item:
                    items.append(item)
            except requests.exceptions.RequestException:
                continue
        return items
