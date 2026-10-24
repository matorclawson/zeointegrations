"""Public GitHub reads through an injected Broker transport; no credential custody.

These package-local types are not Broker operation IDs or a shared Core manifest.
The transport must be supplied by the receiving Broker, never discovered locally.
"""

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote


class Refused(ValueError):
    """The input, public provenance, or provider result cannot be accepted."""


@dataclass(frozen=True)
class Response:
    status: int
    data: object


class Transport(Protocol):
    def get(self, path: str) -> Response:
        """Return a Broker-mediated response without exposing credentials."""


@dataclass(frozen=True)
class Repository:
    full_name: str
    url: str
    description: str | None


@dataclass(frozen=True)
class Issue:
    repository: str
    number: int
    url: str
    title: str
    state: str
    body_summary: str


def _segment(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 100
        or value in {".", ".."}
        or any(not (c.isascii() and (c.isalnum() or c in "._-")) for c in value)
    ):
        raise Refused("invalid repository identity")
    return quote(value, safe="")


def _object(response: Response) -> dict:
    # Never forward a provider error body, headers, token, or arbitrary payload.
    if type(response.status) is not int or response.status != 200:
        raise Refused("provider read refused")
    if not isinstance(response.data, dict):
        raise Refused("invalid provider result")
    return response.data


def _text(value: object, maximum: int) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise Refused("invalid provider text")
    return value


def get_repository(transport: Transport, owner: str, repo: str) -> Repository:
    """Project a public repository response into a closed, credential-free value."""
    identity = f"{_segment(owner)}/{_segment(repo)}"
    data = _object(transport.get(f"/repos/{identity}"))
    url = f"https://github.com/{identity}"
    if (
        data.get("private") is not False
        or data.get("full_name") != identity
        or data.get("html_url") != url
    ):
        raise Refused("repository public provenance mismatch")
    description = data.get("description")
    if description is not None:
        description = _text(description, 4096)
    return Repository(identity, url, description)


def get_issue(transport: Transport, owner: str, repo: str, number: int) -> Issue:
    """Read an issue only after the same transport establishes a public repository.

    Pull requests and redirects are deliberately refused in this bounded slice.
    Public provenance is checked on every call; no cached grant is manufactured.
    """
    if type(number) is not int or not 1 <= number <= 2**63 - 1:
        raise Refused("invalid issue number")
    repository = get_repository(transport, owner, repo)
    data = _object(transport.get(f"/repos/{repository.full_name}/issues/{number}"))
    url = f"{repository.url}/issues/{number}"
    if (
        type(data.get("number")) is not int
        or data["number"] != number
        or data.get("html_url") != url
        or data.get("state") not in ("open", "closed")
        or "pull_request" in data
    ):
        raise Refused("issue provenance or state mismatch")
    title = _text(data.get("title"), 1024)
    body = data.get("body")
    if body is None:
        body = ""
    body = _text(body, 262144)
    return Issue(repository.full_name, number, url, title, data["state"], body[:4096])
