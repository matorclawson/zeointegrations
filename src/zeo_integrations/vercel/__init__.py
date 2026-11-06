"""Bounded vercel operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import VercelClient


class Client(BaseClient):
    provider = "vercel"
    implementation = VercelClient
    origins = ("https://api.vercel.com",)
    operations = (
        "list_deployments",
        "get_deployment",
        "delete_deployment",
        "cancel_deployment",
        "get_deployment_files",
        "get_user",
        "get_deployment_events",
        "add_domain_to_project",
        "create_project",
        "delete_project",
        "get_project",
        "get_project_domain",
        "list_projects",
        "get_project_domains",
        "verify_project_domain",
        "update_project",
        "create_deployment",
    )
