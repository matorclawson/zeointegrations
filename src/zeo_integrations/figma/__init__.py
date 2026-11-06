"""Bounded figma operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import FigmaClient


class Client(BaseClient):
    provider = "figma"
    implementation = FigmaClient
    origins = ("https://api.figma.com",)
    operations = (
        "get_file",
        "get_file_nodes",
        "get_image",
        "get_file_components",
        "get_component_sets",
        "get_styles",
        "get_me",
        "get_team_projects",
        "get_team_components",
        "get_team_component_sets",
        "get_team_styles",
        "get_project_files",
    )
