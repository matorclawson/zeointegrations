"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/linkedin/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

import re
from typing import Any

from zeo_integrations._http.runtime import HTTPException


class LinkedInClient:
    BASE_URL = "https://linkedin-api8.p.rapidapi.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"x-rapidapi-host": "linkedin-api8.p.rapidapi.com"}
        self.username = None

    @staticmethod
    def parse_linkedin_username(username_input: str) -> str:
        """
        Parse LinkedIn username from various formats:
        - @username
        - https://www.linkedin.com/in/username
        - http://linkedin.com/in/username
        - linkedin.com/in/username
        - www.linkedin.com/in/username
        - username

        Returns the clean username without @ or URL components.
        """
        if not username_input:
            return ""
        if username_input.startswith("@"):
            username_input = username_input[1:]
        linkedin_url_pattern = (
            "(?:https?:\\/\\/)?(?:www\\.)?linkedin\\.com\\/in\\/([a-zA-Z0-9\\-]+)"
        )
        url_match = re.search(linkedin_url_pattern, username_input)
        if url_match:
            return url_match.group(1)
        return username_input.strip()

    def set_username(self, username: str):
        """Set the authenticated username for get_me calls"""
        self.username = self.parse_linkedin_username(username)

    def get_me(self) -> dict[str, Any]:
        """Get the authenticated user's profile based on the stored username."""
        if not self.username:
            raise HTTPException(
                status_code=401,
                detail="Username must be configured.",
            )
        return self.get_profile(self.username)

    def get_profile(self, username: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/", headers=self.headers, params={"username": username}
        )
        response.raise_for_status()
        return response.json()

    def search_people(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/search-people", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_profile_posts(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/get-profile-posts", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_connection_count(self, username: str) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/connection-count",
            headers=self.headers,
            params={"username": username},
        )
        response.raise_for_status()
        return response.json()

    def get_post_comments(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/get-post-comments", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_similar_profiles(self, url: str) -> dict[str, Any]:
        params = {"url": url}
        response = self._http.get(
            f"{self.BASE_URL}/similar-profiles", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_company_details(self, username: str) -> dict[str, Any]:
        params = {"username": username}
        response = self._http.get(
            f"{self.BASE_URL}/get-company-details", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def search_companies(self, payload: dict[str, Any]) -> dict[str, Any]:
        post_headers = self.headers.copy()
        post_headers["Content-Type"] = "application/json"
        response = self._http.post(
            f"{self.BASE_URL}/companies/search", headers=post_headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_company_jobs(self, payload: dict[str, Any]) -> dict[str, Any]:
        post_headers = self.headers.copy()
        post_headers["Content-Type"] = "application/json"
        response = self._http.post(
            f"{self.BASE_URL}/company-jobs", headers=post_headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_company_posts(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        response = self._http.get(
            f"{self.BASE_URL}/get-company-posts", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_company_post_comments(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        response = self._http.get(
            f"{self.BASE_URL}/get-company-post-comments",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def search_posts(self, payload: dict[str, Any]) -> dict[str, Any]:
        post_headers = self.headers.copy()
        post_headers["Content-Type"] = "application/json"
        response = self._http.post(
            f"{self.BASE_URL}/search-posts", headers=post_headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_post(self, url: str) -> dict[str, Any]:
        params = {"url": url}
        response = self._http.get(
            f"{self.BASE_URL}/get-post", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def get_job_details(self, job_id: str) -> dict[str, Any]:
        params = {"id": job_id}
        response = self._http.get(
            f"{self.BASE_URL}/get-job-details", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def search_jobs(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._http.get(
            f"{self.BASE_URL}/search-jobs", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()

    def search_locations(self, keyword: str) -> dict[str, Any]:
        params = {"keyword": keyword}
        response = self._http.get(
            f"{self.BASE_URL}/search-locations", headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()
