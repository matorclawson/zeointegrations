"""Bounded svgl operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import SvglClient


class Client(BaseClient):
    provider = "svgl"
    implementation = SvglClient
    origins = ("https://api.svgl.app",)
    operations = (
        "get_all_svgs",
        "get_svg_by_category",
        "get_categories",
        "search_svgs",
    )
