"""Selected operations from pinned VeyraX; MIT. See NOTICE."""

from zeo_integrations._http import Client as BaseClient


class _Operations:
    def __init__(self, transport):
        self.http = transport

    def list_channels(self, parameters: dict):
        return self.http.get(
            "https://slack.com/api/conversations.list", params=parameters
        ).json()

    def channel_history(self, parameters: dict):
        return self.http.get(
            "https://slack.com/api/conversations.history", params=parameters
        ).json()

    def user_info(self, parameters: dict):
        return self.http.get(
            "https://slack.com/api/users.info", params=parameters
        ).json()

    def post_message(self, parameters: dict):
        return self.http.post(
            "https://slack.com/api/chat.postMessage", json=parameters
        ).json()

    def open_conversation(self, parameters: dict):
        return self.http.post(
            "https://slack.com/api/conversations.open", json=parameters
        ).json()


class Client(BaseClient):
    provider = "slack"
    implementation = _Operations
    origins = ("https://slack.com",)
    operations = (
        "list_channels",
        "channel_history",
        "user_info",
        "post_message",
        "open_conversation",
    )
