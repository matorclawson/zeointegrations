"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/trello/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any


class TrelloClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.trello.com/1"
        self.auth_params = {}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] = None,
        data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        request_params = {**self.auth_params}
        if params:
            request_params.update(params)
        response = self._http.request(
            method=method, url=url, params=request_params, json=data
        )
        response.raise_for_status()
        return response.json()

    def get_cards(
        self, board_id: str, list_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        params = {}
        if limit:
            params["limit"] = limit
        if list_id:
            return self._make_request("GET", f"lists/{list_id}/cards", params=params)
        else:
            return self._make_request("GET", f"boards/{board_id}/cards", params=params)

    def get_card(self, card_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"cards/{card_id}")

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str | None = None,
        pos: str | None = "bottom",
        due: str | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        params = {"idList": list_id, "name": name}
        if desc:
            params["desc"] = desc
        if pos:
            params["pos"] = pos
        if due:
            params["due"] = due
        if label_ids:
            params["idLabels"] = ",".join(label_ids)
        return self._make_request("POST", "cards", params=params)

    def update_card(self, card_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._make_request("PUT", f"cards/{card_id}", params=data)

    def delete_card(self, card_id: str) -> dict[str, Any]:
        return self._make_request("DELETE", f"cards/{card_id}")

    def get_boards(self, member_id: str = "me") -> list[dict[str, Any]]:
        return self._make_request("GET", f"members/{member_id}/boards")

    def get_board(self, board_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"boards/{board_id}")

    def get_lists(self, board_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"boards/{board_id}/lists")

    def get_list(self, list_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"lists/{list_id}")

    def get_labels(self, board_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"boards/{board_id}/labels")

    def get_label(self, label_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"labels/{label_id}")

    def get_board_members(self, board_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"boards/{board_id}/members")

    def get_member(self, member_id: str = "me") -> dict[str, Any]:
        return self._make_request("GET", f"members/{member_id}")

    def get_card_checklists(self, card_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"cards/{card_id}/checklists")

    def create_checklist(self, card_id: str, name: str) -> dict[str, Any]:
        params = {"name": name}
        return self._make_request("POST", f"cards/{card_id}/checklists", params=params)

    def create_checklist_item(
        self, checklist_id: str, name: str, checked: bool = False
    ) -> dict[str, Any]:
        params = {"name": name, "checked": "true" if checked else "false"}
        return self._make_request(
            "POST", f"checklists/{checklist_id}/checkItems", params=params
        )

    def get_organizations(self, member_id: str = "me") -> list[dict[str, Any]]:
        return self._make_request("GET", f"members/{member_id}/organizations")

    def get_organization(self, org_id: str) -> dict[str, Any]:
        return self._make_request("GET", f"organizations/{org_id}")

    def get_organization_boards(self, org_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"organizations/{org_id}/boards")

    def get_organization_members(self, org_id: str) -> list[dict[str, Any]]:
        return self._make_request("GET", f"organizations/{org_id}/members")
