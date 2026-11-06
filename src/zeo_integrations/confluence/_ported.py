"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/confluence/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any

from zeo_integrations._http import compatibility as requests
from zeo_integrations._http.runtime import HTTPException


class ConfluenceClient:
    def __init__(self, transport, cloud_id: str):
        self._http = transport
        self.session = self._http
        self.base_url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/rest/api"

    def _initialize_client(self):
        try:
            resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
            response = self.session.get(
                resources_url, headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            resources = response.json()
            if not resources:
                raise HTTPException(
                    status_code=404, detail="No Confluence resources available"
                )
            self.cloud_id = resources[0]["id"]
            self.base_url = (
                f"https://api.atlassian.com/ex/confluence/{self.cloud_id}/rest/api"
            )
            self.web_url = f"{resources[0]['url']}/wiki"
            self.session.headers.update(
                {"Content-Type": "application/json", "Accept": "application/json"}
            )
        except requests.exceptions.HTTPError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Provider rejected request",
            ) from None
        except Exception:
            raise HTTPException(
                status_code=500, detail="Provider rejected request"
            ) from None

    def list_spaces(self, **kwargs) -> dict[str, Any]:
        return self._make_request("GET", "/space", params=kwargs)

    def list_pages(self, **kwargs) -> dict[str, Any]:
        return self._make_request(
            "GET",
            "/content",
            params={
                **kwargs,
                "type": "page",
                "expand": "space,version,body.storage,ancestors",
            },
        )

    def get_page(self, page_id: str) -> dict[str, Any]:
        return self._make_request(
            "GET",
            f"/content/{page_id}",
            params={"expand": "space,version,body.storage,ancestors"},
        )

    def create_page(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("POST", "/content", data=data)

    def update_page(self, page_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("PUT", f"/content/{page_id}", data=data)

    def search_content(self, **kwargs) -> dict[str, Any]:
        return self._make_request("GET", "/content", params=kwargs)

    def delete_page(self, page_id: str) -> None:
        return self._make_request("DELETE", f"/content/{page_id}")

    def _make_request(self, method, endpoint, params=None, data=None):
        if self.base_url is None:
            self._initialize_client()
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, params=params, json=data)
        response.raise_for_status()
        if method == "DELETE" or not response.content:
            return {}
        return response.json()
