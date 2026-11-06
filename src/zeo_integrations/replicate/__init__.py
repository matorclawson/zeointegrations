"""Bounded replicate operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import ReplicateClient


class Client(BaseClient):
    provider = "replicate"
    implementation = ReplicateClient
    origins = ("https://api.replicate.com",)
    operations = (
        "get_account",
        "create_prediction",
        "list_predictions",
        "get_prediction",
        "cancel_prediction",
        "create_deployment_prediction",
        "list_deployments",
        "get_deployment",
        "create_deployment",
        "update_deployment",
        "delete_deployment",
        "create_official_model_prediction",
        "list_models",
        "get_model",
        "create_model",
        "delete_model",
        "list_model_examples",
        "get_model_readme",
        "list_model_versions",
        "get_model_version",
        "delete_model_version",
        "create_training",
        "list_trainings",
        "get_training",
        "cancel_training",
        "list_collections",
        "get_collection",
        "list_hardware",
    )
