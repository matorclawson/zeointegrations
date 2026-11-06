"""Bounded coda operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import CodaClient


class Client(BaseClient):
    provider = "coda"
    implementation = CodaClient
    origins = ("https://coda.io",)
    operations = (
        "list_docs",
        "get_doc",
        "list_pages",
        "get_page",
        "create_page",
        "update_page",
        "delete_page",
        "export_page",
        "get_export_status",
        "list_tables",
        "get_table",
        "list_columns",
        "get_column",
        "list_rows",
        "get_row",
        "create_rows",
        "update_row",
        "delete_rows",
        "delete_row",
        "push_button",
        "list_formulas",
        "get_formula",
        "list_controls",
        "get_control",
        "get_whoami",
    )
