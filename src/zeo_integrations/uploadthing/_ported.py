"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/uploadthing/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class UploadThingClient:
    BASE_URL = "https://api.uploadthing.com"

    def __init__(self, transport):
        self._http = transport
        self.headers = {"Content-Type": "application/json"}

    def list_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to list files"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/listFiles", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def poll_upload(self, file_key: str) -> dict[str, Any]:
        """Low-level API call to poll for upload completion status"""
        response = self._http.get(
            f"{self.BASE_URL}/v6/pollUpload/{file_key}", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_server_callback(self, auth_token: str) -> dict[str, Any]:
        """Low-level API call to get server callback data"""
        headers = {**self.headers}
        response = self._http.get(f"{self.BASE_URL}/v6/serverCallback", headers=headers)
        response.raise_for_status()
        return response.json()

    def set_server_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to set server callback data"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/serverCallback", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def prepare_upload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to prepare uploads and get presigned URLs"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/prepareUpload", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def upload_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to upload files directly without a file route"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/uploadFiles", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def rename_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to rename files"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/renameFiles", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def delete_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Low-level API call to delete files"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/deleteFiles", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_app_info(self) -> dict[str, Any]:
        """Low-level API call to get app info"""
        response = self._http.post(
            f"{self.BASE_URL}/v7/getAppInfo", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_usage_info(self) -> dict[str, Any]:
        """Low-level API call to get usage info"""
        response = self._http.post(
            f"{self.BASE_URL}/v6/getUsageInfo", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> bool:
        """Test the API connection using a minimal limit value"""
        try:
            self.list_files({"limit": 1})
            return True
        except Exception:
            return False
