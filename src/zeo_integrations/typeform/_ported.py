"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/typeform/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class TypeformClient:
    """Client for interacting with the Typeform API."""

    BASE_URL = "https://api.typeform.com"

    def __init__(self, transport):
        self._http = transport
        (
            "Initialize the Typeform client with authentication.\n        "
            "\n        Args:\n            access_token (str): The Typeform "
            "API access token\n        "
        )
        self.headers = {"Content-Type": "application/json"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Typeform API.

        Args:
            method (str): HTTP method (GET, POST, PATCH, DELETE)
            endpoint (str): API endpoint path
            params (Dict[str, Any], optional): Query parameters
            data (Dict[str, Any], optional): Request body data

        Returns:
            Dict[str, Any]: Response from the API

        Raises:
            RequestException: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = self._http.request(
            method=method, url=url, headers=self.headers, params=params, json=data
        )
        response.raise_for_status()
        if method == "DELETE" and response.status_code == 204:
            return {}
        if response.content:
            return response.json()
        return {}

    def get_account_workspaces(
        self,
        account_id: str,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve all workspaces in a specific account.

        Args:
            account_id (str): ID of the account
            search (str, optional): Filter results by name
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of results per page

        Returns:
            Dict[str, Any]: List of workspaces and pagination info
        """
        params = {}
        if search:
            params["search"] = search
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        return self._make_request(
            "GET", f"/accounts/{account_id}/workspaces", params=params
        )

    def create_account_workspace(self, account_id: str, name: str) -> dict[str, Any]:
        """Create a workspace in a specific account.

        Args:
            account_id (str): ID of the account
            name (str): Name of the new workspace

        Returns:
            Dict[str, Any]: Created workspace details
        """
        data = {"name": name}
        return self._make_request(
            "POST", f"/accounts/{account_id}/workspaces", data=data
        )

    def get_workspaces(
        self,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve all workspaces the user has access to across all accounts.

        Args:
            search (str, optional): Filter results by name
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of results per page

        Returns:
            Dict[str, Any]: List of workspaces and pagination info
        """
        params = {}
        if search:
            params["search"] = search
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        return self._make_request("GET", "/workspaces", params=params)

    def create_workspace(self, name: str) -> dict[str, Any]:
        """Create a workspace in the account where the user is owner.

        Args:
            name (str): Name of the new workspace

        Returns:
            Dict[str, Any]: Created workspace details
        """
        data = {"name": name}
        return self._make_request("POST", "/workspaces", data=data)

    def delete_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Delete a workspace.

        Args:
            workspace_id (str): ID of the workspace to delete

        Returns:
            Dict[str, Any]: Empty dict for successful deletion
        """
        return self._make_request("DELETE", f"/workspaces/{workspace_id}")

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        """Retrieve a specific workspace.

        Args:
            workspace_id (str): ID of the workspace

        Returns:
            Dict[str, Any]: Workspace details
        """
        return self._make_request("GET", f"/workspaces/{workspace_id}")

    def update_workspace(
        self, workspace_id: str, operations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Update a workspace using JSON Patch operations.

        Args:
            workspace_id (str): ID of the workspace to update
            operations (List[Dict[str, Any]]): List of patch operations to apply

        Returns:
            Dict[str, Any]: Empty dict for successful update
        """
        return self._make_request(
            "PATCH", f"/workspaces/{workspace_id}", data=operations
        )

    def get_forms(
        self,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        workspace_id: str | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve all forms in your Typeform account.

        Args:
            search (str, optional): Filter results by name
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of results per page
            workspace_id (str, optional): Filter forms by workspace
            sort_by (str, optional): Field to sort by (created_at or last_updated_at)
            order_by (str, optional): Sort order (asc or desc)

        Returns:
            Dict[str, Any]: List of forms and pagination info
        """
        params = {}
        if search:
            params["search"] = search
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        if workspace_id:
            params["workspace_id"] = workspace_id
        if sort_by:
            params["sort_by"] = sort_by
        if order_by:
            params["order_by"] = order_by
        return self._make_request("GET", "/forms", params=params)

    def create_form(self, form_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new form.

        Args:
            form_data (Dict[str, Any]): Complete form definition.

        Returns:
            Dict[str, Any]: Created form details
        """
        return self._make_request("POST", "/forms", data=form_data)

    def delete_form(self, form_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/forms/{form_id}")

    def get_form(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}")

    def update_form_patch(
        self, form_id: str, operations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return self._make_request("PATCH", f"/forms/{form_id}", data=operations)

    def update_form(self, form_id: str, form_data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("PUT", f"/forms/{form_id}", data=form_data)

    def get_form_messages(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/messages")

    def update_form_messages(
        self, form_id: str, messages: dict[str, str]
    ) -> dict[str, Any]:
        return self._make_request("PUT", f"/forms/{form_id}/messages", data=messages)

    def get_translation_payload(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/translations/main")

    def get_translation_statuses(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/translations/status")

    def delete_form_translation(self, form_id: str, language: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/forms/{form_id}/translations/{language}")

    def get_form_translation(self, form_id: str, language: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/translations/{language}")

    def update_form_translation(
        self, form_id: str, language: str, translation_data: dict[str, Any]
    ) -> dict[str, Any]:
        return self._make_request(
            "PUT", f"/forms/{form_id}/translations/{language}", data=translation_data
        )

    def auto_translate_form(self, form_id: str, language: str) -> dict[str, Any]:
        return self._make_request(
            "POST", f"/forms/{form_id}/translations/{language}/auto"
        )

    def get_images(self) -> list[dict[str, Any]]:
        return self._make_request("GET", "/images")

    def delete_image(self, image_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/images/{image_id}")

    def get_image(self, image_id: str, json_response: bool = True) -> dict[str, Any]:
        headers = self.headers.copy()
        if json_response:
            headers["Accept"] = "application/json"
        url = f"{self.BASE_URL}/images/{image_id}"
        response = self._http.get(url, headers=headers)
        response.raise_for_status()
        if json_response:
            return response.json()
        else:
            return {
                "content": response.content,
                "media_type": response.headers.get("Content-Type"),
            }

    def get_background_image(
        self, image_id: str, size: str, json_response: bool = True
    ) -> dict[str, Any]:
        headers = self.headers.copy()
        if json_response:
            headers["Accept"] = "application/json"
        url = f"{self.BASE_URL}/images/{image_id}/background/{size}"
        response = self._http.get(url, headers=headers)
        response.raise_for_status()
        if json_response:
            return response.json()
        else:
            return {
                "content": response.content,
                "media_type": response.headers.get("Content-Type"),
            }

    def get_choice_image(
        self, image_id: str, size: str, json_response: bool = True
    ) -> dict[str, Any]:
        headers = self.headers.copy()
        if json_response:
            headers["Accept"] = "application/json"
        url = f"{self.BASE_URL}/images/{image_id}/choice/{size}"
        response = self._http.get(url, headers=headers)
        response.raise_for_status()
        if json_response:
            return response.json()
        else:
            return {
                "content": response.content,
                "media_type": response.headers.get("Content-Type"),
            }

    def get_image_by_size(
        self, image_id: str, size: str, json_response: bool = True
    ) -> dict[str, Any]:
        headers = self.headers.copy()
        if json_response:
            headers["Accept"] = "application/json"
        url = f"{self.BASE_URL}/images/{image_id}/image/{size}"
        response = self._http.get(url, headers=headers)
        response.raise_for_status()
        if json_response:
            return response.json()
        else:
            return {
                "content": response.content,
                "media_type": response.headers.get("Content-Type"),
            }

    def get_themes(
        self, page: int | None = None, page_size: int | None = None
    ) -> dict[str, Any]:
        params = {}
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        return self._make_request("GET", "/themes", params=params)

    def create_theme(self, theme_data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("POST", "/themes", data=theme_data)

    def delete_theme(self, theme_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/themes/{theme_id}")

    def get_theme(self, theme_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/themes/{theme_id}")

    def update_theme_partial(
        self, theme_id: str, theme_updates: dict[str, Any]
    ) -> dict[str, Any]:
        return self._make_request("PATCH", f"/themes/{theme_id}", data=theme_updates)

    def update_theme_full(
        self, theme_id: str, theme_data: dict[str, Any]
    ) -> dict[str, Any]:
        return self._make_request("PUT", f"/themes/{theme_id}", data=theme_data)

    def delete_responses(self, form_id: str, response_ids: list[str]) -> dict[str, Any]:
        data = {"included_response_ids": response_ids}
        return self._make_request("DELETE", f"/forms/{form_id}/responses", data=data)

    def get_responses(
        self,
        form_id: str,
        page_size: int | None = None,
        since: str | None = None,
        until: str | None = None,
        after: str | None = None,
        before: str | None = None,
        included_response_ids: list[str] | None = None,
        excluded_response_ids: list[str] | None = None,
        response_type: list[str] | None = None,
        completed: bool | None = None,
        sort: str | None = None,
        query: str | None = None,
        fields: list[str] | None = None,
        answered_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        params = {}
        if page_size:
            params["page_size"] = page_size
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if included_response_ids:
            params["included_response_ids"] = ",".join(included_response_ids)
        if excluded_response_ids:
            params["excluded_response_ids"] = ",".join(excluded_response_ids)
        if response_type:
            params["response_type"] = ",".join(response_type)
        if completed is not None:
            params["completed"] = str(completed).lower()
        if sort:
            params["sort"] = sort
        if query:
            params["query"] = query
        if fields:
            params["fields"] = ",".join(fields)
        if answered_fields:
            params["answered_fields"] = ",".join(answered_fields)
        return self._make_request("GET", f"/forms/{form_id}/responses", params=params)

    def download_form_files(self, form_id: str) -> bytes:
        url = f"{self.BASE_URL}/forms/{form_id}/responses/files"
        response = self._http.get(url, headers=self.headers)
        response.raise_for_status()
        return response.content

    def get_response_file(
        self,
        form_id: str,
        response_id: str,
        field_id: str,
        filename: str,
        inline: bool = False,
    ) -> bytes:
        params = {}
        if inline:
            params["inline"] = "true"
        url = (
            f"{self.BASE_URL}/forms/{form_id}/responses/{response_id}/"
            f"fields/{field_id}/files/{filename}"
        )
        response = self._http.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.content

    def get_form_insights(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/insights/{form_id}/summary")

    def get_webhooks(self, form_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/webhooks")

    def get_webhook(self, form_id: str, tag: str) -> dict[str, Any]:
        return self._make_request("GET", f"/forms/{form_id}/webhooks/{tag}")

    def create_or_update_webhook(
        self, form_id: str, tag: str, webhook_data: dict[str, Any]
    ) -> dict[str, Any]:
        return self._make_request(
            "PUT", f"/forms/{form_id}/webhooks/{tag}", data=webhook_data
        )

    def delete_webhook(self, form_id: str, tag: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"/forms/{form_id}/webhooks/{tag}")
