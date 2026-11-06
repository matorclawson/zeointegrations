"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/dropbox/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

import json
from typing import IO, Any

from .schema import Access, Audience, RequestedVisibility


class DropboxClient:
    BASE_URL = "https://api.dropboxapi.com/2"
    CONTENT_URL = "https://content.dropboxapi.com/2"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def list_files(self, path: str = "", **kwargs) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/list_folder"
        if path is None:
            path = ""
        data = {
            "path": path,
            "recursive": False,
            "include_media_info": False,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            **kwargs,
        }
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_file_metadata(self, path: str) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/get_metadata"
        path = f"/{path.strip('/')}"
        data = {"path": path}
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_folder(self, path: str, autorename: bool = False) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/create_folder_v2"
        data = {"path": path, "autorename": autorename}
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def upload_file(
        self, path: str, file_content: IO, mode: str = "add"
    ) -> dict[str, Any]:
        endpoint = f"{self.CONTENT_URL}/files/upload"
        headers = {
            "Dropbox-API-Arg": json.dumps(
                {"path": path, "mode": mode, "autorename": True}
            ),
            "Content-Type": "application/octet-stream",
        }
        response = self._http.post(endpoint, headers=headers, data=file_content)
        response.raise_for_status()
        return response.json()

    def download_file(self, path: str) -> tuple[bytes, dict[str, Any]]:
        endpoint = f"{self.CONTENT_URL}/files/download"
        path = f"/{path.strip('/')}"
        headers = {"Dropbox-API-Arg": json.dumps({"path": path})}
        response = self._http.post(endpoint, headers=headers)
        response.raise_for_status()
        metadata = json.loads(response.headers["Dropbox-API-Result"])
        return (response.content, metadata)

    def delete_file(self, path: str) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/delete_v2"
        data = {"path": path}
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def move_file(self, from_path: str, to_path: str) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/move_v2"
        data = {
            "from_path": from_path,
            "to_path": to_path,
            "allow_shared_folder": True,
            "autorename": False,
            "allow_ownership_transfer": False,
        }
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_shared_link(
        self, path: str, settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/sharing/create_shared_link_with_settings"
        if settings is None:
            settings = {
                "requested_visibility": RequestedVisibility.PUBLIC.value,
                "audience": Audience.PUBLIC.value,
                "access": Access.VIEWER.value,
                "allow_download": True,
            }
        if settings and isinstance(settings, dict):
            for key in ["requested_visibility", "audience", "access"]:
                if key in settings and hasattr(settings[key], "value"):
                    settings[key] = settings[key].value
        data = {"path": path, "settings": settings}
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def search_files(
        self,
        query: str,
        path: str = "",
        max_results: int = 20,
        filename_only: bool = False,
        file_status: str = "active",
    ) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/search_v2"
        data = {
            "query": query,
            "options": {
                "path": path,
                "max_results": max_results,
                "filename_only": filename_only,
                "file_status": file_status,
            },
            "match_field_options": {"include_highlights": False},
        }
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def search_continue(self, cursor: str) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/files/search/continue_v2"
        data = {"cursor": cursor}
        response = self._http.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
