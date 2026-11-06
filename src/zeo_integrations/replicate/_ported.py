"""MIT port of VeyraX provider operations; custody removed.
Source: VeyraX/veyrax-platform@1cdddde9d5d76b9891896ca78a95e069647e81df
Path: aci_server/integrations/replicate/client.py
Copyright VeyraX contributors. See NOTICE and VeyraX-LICENSE.
"""

from typing import Any

from zeo_integrations._http.runtime import HTTPError


class ReplicateClient:
    def __init__(self, transport):
        self._http = transport
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {"Content-Type": "application/json"}

    def _prepare_wait_header(
        self, headers: dict[str, str], wait: int | None = None
    ) -> dict[str, str]:
        """
        Utility function to prepare headers with wait parameter if provided.
        Ensures wait time is within allowed limits (1-60 seconds).

        Args:
            headers: The current headers dictionary
            wait: Optional wait time in seconds

        Returns:
            Updated headers dictionary
        """
        if wait is not None:
            if wait > 60:
                wait = 60
            elif wait < 1:
                wait = 1
            headers["Prefer"] = f"wait={wait}"
        return headers

    def get_account(self) -> dict[str, Any]:
        """
        Get information about the authenticated account
        """
        response = self._http.get(f"{self.base_url}/account", headers=self.headers)
        return response.json()

    def create_prediction(
        self, data: dict[str, Any], wait: int | None = None
    ) -> dict[str, Any]:
        """
        Create a prediction with the specified model version and parameters
        """
        headers = self.headers.copy()
        headers = self._prepare_wait_header(headers, wait)
        response = self._http.post(
            f"{self.base_url}/predictions", headers=headers, json=data
        )
        return response.json()

    def list_predictions(self, params: dict[str, Any] = None) -> dict[str, Any]:
        """
        List all predictions created by the authenticated user
        """
        response = self._http.get(
            f"{self.base_url}/predictions", headers=self.headers, params=params
        )
        return response.json()

    def get_prediction(self, prediction_id: str) -> dict[str, Any]:
        """
        Get the current state of a prediction
        """
        response = self._http.get(
            f"{self.base_url}/predictions/{prediction_id}", headers=self.headers
        )
        return response.json()

    def cancel_prediction(self, prediction_id: str) -> dict[str, Any]:
        """
        Cancel a running prediction
        """
        response = self._http.post(
            f"{self.base_url}/predictions/{prediction_id}/cancel", headers=self.headers
        )
        return response.json()

    def create_deployment_prediction(
        self,
        deployment_owner: str,
        deployment_name: str,
        data: dict[str, Any],
        wait: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a prediction using a deployment
        """
        headers = self.headers.copy()
        headers = self._prepare_wait_header(headers, wait)
        response = self._http.post(
            f"{self.base_url}/deployments/{deployment_owner}/{deployment_name}/predictions",
            headers=headers,
            json=data,
        )
        return response.json()

    def list_deployments(self) -> dict[str, Any]:
        """
        List all deployments for the authenticated account
        """
        response = self._http.get(f"{self.base_url}/deployments", headers=self.headers)
        return response.json()

    def get_deployment(
        self, deployment_owner: str, deployment_name: str
    ) -> dict[str, Any]:
        """
        Get information about a deployment
        """
        response = self._http.get(
            f"{self.base_url}/deployments/{deployment_owner}/{deployment_name}",
            headers=self.headers,
        )
        return response.json()

    def create_deployment(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new deployment
        """
        response = self._http.post(
            f"{self.base_url}/deployments", headers=self.headers, json=data
        )
        return response.json()

    def update_deployment(
        self, deployment_owner: str, deployment_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update an existing deployment
        """
        response = self._http.patch(
            f"{self.base_url}/deployments/{deployment_owner}/{deployment_name}",
            headers=self.headers,
            json=data,
        )
        return response.json()

    def delete_deployment(
        self, deployment_owner: str, deployment_name: str
    ) -> dict[str, Any]:
        """
        Delete a deployment
        """
        response = self._http.delete(
            f"{self.base_url}/deployments/{deployment_owner}/{deployment_name}",
            headers=self.headers,
        )
        return {} if not response.content else response.json()

    def create_official_model_prediction(
        self,
        model_owner: str,
        model_name: str,
        data: dict[str, Any],
        wait: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a prediction using an official model
        """
        headers = self.headers.copy()
        headers = self._prepare_wait_header(headers, wait)
        is_minimax_video = model_owner == "minimax" and model_name == "video-01"
        if is_minimax_video:
            if "input" in data:
                data = {"input": data["input"]}
        try:
            url = f"{self.base_url}/models/{model_owner}/{model_name}/predictions"
            response = self._http.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            return response_data
        except HTTPError as e:
            if is_minimax_video:
                pass
                if hasattr(e, "response"):
                    pass
                    try:
                        pass
                    except Exception:
                        pass
            try:
                error_json = e.response.json()
                if is_minimax_video:
                    pass
                return error_json
            except Exception:
                return {
                    "error": True,
                    "detail": str(e),
                    "status_code": e.response.status_code
                    if hasattr(e, "response")
                    else 500,
                }
        except Exception as e:
            pass
            if is_minimax_video:
                pass
            return {"error": True, "detail": str(e)}

    def list_models(self) -> dict[str, Any]:
        """
        List all public models
        """
        response = self._http.get(f"{self.base_url}/models", headers=self.headers)
        return response.json()

    def get_model(self, model_owner: str, model_name: str) -> dict[str, Any]:
        """
        Get information about a model
        """
        response = self._http.get(
            f"{self.base_url}/models/{model_owner}/{model_name}", headers=self.headers
        )
        return response.json()

    def create_model(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new model
        """
        response = self._http.post(
            f"{self.base_url}/models", headers=self.headers, json=data
        )
        return response.json()

    def delete_model(self, model_owner: str, model_name: str) -> dict[str, Any]:
        """
        Delete a model
        """
        response = self._http.delete(
            f"{self.base_url}/models/{model_owner}/{model_name}", headers=self.headers
        )
        return {} if not response.content else response.json()

    def search_models(self, query: str) -> dict[str, Any]:
        """
        Search for models matching a query
        """
        headers = self.headers.copy()
        headers["Content-Type"] = "text/plain"
        response = self._http.request(
            "QUERY", f"{self.base_url}/models", headers=headers, data=query
        )
        return response.json()

    def list_model_examples(self, model_owner: str, model_name: str) -> dict[str, Any]:
        """
        List examples for a model
        """
        response = self._http.get(
            f"{self.base_url}/models/{model_owner}/{model_name}/examples",
            headers=self.headers,
        )
        return response.json()

    def get_model_readme(self, model_owner: str, model_name: str) -> str:
        """
        Get the README content for a model
        """
        response = self._http.get(
            f"{self.base_url}/models/{model_owner}/{model_name}/readme",
            headers=self.headers,
        )
        return response.text

    def list_model_versions(self, model_owner: str, model_name: str) -> dict[str, Any]:
        """
        List versions for a model
        """
        response = self._http.get(
            f"{self.base_url}/models/{model_owner}/{model_name}/versions",
            headers=self.headers,
        )
        return response.json()

    def get_model_version(
        self, model_owner: str, model_name: str, version_id: str
    ) -> dict[str, Any]:
        """
        Get information about a model version
        """
        response = self._http.get(
            f"{self.base_url}/models/{model_owner}/{model_name}/versions/{version_id}",
            headers=self.headers,
        )
        return response.json()

    def delete_model_version(
        self, model_owner: str, model_name: str, version_id: str
    ) -> dict[str, Any]:
        """
        Delete a model version
        """
        response = self._http.delete(
            f"{self.base_url}/models/{model_owner}/{model_name}/versions/{version_id}",
            headers=self.headers,
        )
        return {} if not response.content else response.json()

    def create_training(
        self, model_owner: str, model_name: str, version_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a new training
        """
        response = self._http.post(
            f"{self.base_url}/models/{model_owner}/{model_name}/versions/{version_id}/trainings",
            headers=self.headers,
            json=data,
        )
        return response.json()

    def list_trainings(self) -> dict[str, Any]:
        """
        List all trainings
        """
        response = self._http.get(f"{self.base_url}/trainings", headers=self.headers)
        return response.json()

    def get_training(self, training_id: str) -> dict[str, Any]:
        """
        Get information about a training
        """
        response = self._http.get(
            f"{self.base_url}/trainings/{training_id}", headers=self.headers
        )
        return response.json()

    def cancel_training(self, training_id: str) -> dict[str, Any]:
        """
        Cancel a training
        """
        response = self._http.post(
            f"{self.base_url}/trainings/{training_id}/cancel", headers=self.headers
        )
        return response.json()

    def list_collections(self) -> dict[str, Any]:
        """
        List collections of models
        """
        response = self._http.get(f"{self.base_url}/collections", headers=self.headers)
        return response.json()

    def get_collection(self, collection_slug: str) -> dict[str, Any]:
        """
        Get a collection of models
        """
        response = self._http.get(
            f"{self.base_url}/collections/{collection_slug}", headers=self.headers
        )
        return response.json()

    def list_hardware(self) -> list[dict[str, Any]]:
        """
        List available hardware for models
        """
        response = self._http.get(f"{self.base_url}/hardware", headers=self.headers)
        return response.json()
