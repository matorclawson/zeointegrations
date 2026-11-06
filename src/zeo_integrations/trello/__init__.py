"""Bounded trello operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import TrelloClient


class Client(BaseClient):
    provider = "trello"
    implementation = TrelloClient
    origins = ("https://api.trello.com",)
    operations = (
        "get_cards",
        "get_card",
        "create_card",
        "update_card",
        "delete_card",
        "get_boards",
        "get_board",
        "get_lists",
        "get_list",
        "get_labels",
        "get_label",
        "get_board_members",
        "get_member",
        "get_card_checklists",
        "create_checklist",
        "create_checklist_item",
        "get_organizations",
        "get_organization",
        "get_organization_boards",
        "get_organization_members",
    )
