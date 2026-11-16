"""Explicit injected Sheets credentials; no auth/config files or live API calls."""

from unittest.mock import MagicMock, patch

import pytest
from zeo_core.core.errors import ZeoApiError

from zeo_integrations.google.sheets import GoogleSheetsService


def test_injected_credentials_read_and_raw_append_without_auth_or_config():
    credentials = MagicMock(name="inert_google_credentials")
    api = MagicMock()
    values = api.spreadsheets.return_value.values.return_value
    values.get.return_value.execute.return_value = {"values": [["fixture"]]}
    values.append.return_value.execute.return_value = {"updates": {"updatedRows": 1}}
    with (
        patch("googleapiclient.discovery.build", return_value=api) as build,
        patch("zeo_integrations.google.sheets.service.GoogleAuthProvider") as auth,
        patch.object(GoogleSheetsService, "_initialize_config") as config,
    ):
        service = GoogleSheetsService.from_credentials(credentials)
        assert service.is_available()
        assert service.initialize().success
        assert service.get_values("fixture-sheet", "Sheet1!A1").content == {
            "values": [["fixture"]]
        }
        assert service.append_values(
            "fixture-sheet", "Sheet1!A1", [["=literal"]], value_input_option="RAW"
        ).success
    build.assert_called_once_with(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
        static_discovery=True,
        num_retries=0,
    )
    auth.assert_not_called()
    config.assert_not_called()
    values.append.assert_called_once_with(
        spreadsheetId="fixture-sheet",
        range="Sheet1!A1",
        body={"range": "Sheet1!A1", "values": [["=literal"]]},
        valueInputOption="RAW",
    )


def test_missing_credentials_never_trigger_default_authentication():
    with patch("googleapiclient.discovery.build") as build:
        with pytest.raises(ZeoApiError):
            GoogleSheetsService.from_credentials(None)
    build.assert_not_called()


def test_sdk_construction_error_does_not_retain_secret_exception():
    with patch(
        "googleapiclient.discovery.build", side_effect=RuntimeError("inert-secret")
    ):
        with pytest.raises(ZeoApiError) as caught:
            GoogleSheetsService.from_credentials(MagicMock())
    assert "inert-secret" not in str(caught.value)
    assert caught.value.__context__ is None


@pytest.mark.parametrize("operation", ["read", "append"])
def test_memory_mode_request_failures_are_redacted_and_not_retried(operation, caplog):
    api = MagicMock()
    values = api.spreadsheets.return_value.values.return_value
    target = values.get if operation == "read" else values.append
    target.return_value.execute.side_effect = RuntimeError("inert-secret")
    with patch("googleapiclient.discovery.build", return_value=api):
        service = GoogleSheetsService.from_credentials(MagicMock())
        result = (
            service.get_values("fixture", "A1")
            if operation == "read"
            else service.append_values("fixture", "A1", [["hello"]], "RAW")
        )
    assert not result.success
    assert "inert-secret" not in str(result.error)
    assert "inert-secret" not in caplog.text
    target.return_value.execute.assert_called_once_with()
