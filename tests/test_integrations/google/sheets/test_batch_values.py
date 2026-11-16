"""Synthetic multi-range reads; no provider, credentials or network access."""

from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from zeo_integrations.google.sheets import (
    GoogleSheetsService,
    SheetsBatchGetRequest,
    SheetsBatchGetResponse,
    SheetsValueRange,
)


@pytest.fixture
def wired():
    api = MagicMock()
    resource = api.spreadsheets.return_value.values.return_value
    resource.batchGet.return_value.execute.return_value = {
        "spreadsheetId": "fixture-book",
        "valueRanges": [
            {"range": "First!A1:B2", "majorDimension": "ROWS", "values": [[1, True]]},
            {"range": "Empty!A1", "majorDimension": "ROWS"},
        ],
    }
    with patch("googleapiclient.discovery.build", return_value=api):
        service = GoogleSheetsService.from_credentials(MagicMock())
    return service, resource


def test_ordered_ranges_and_omitted_empty_cells(wired):
    service, resource = wired
    result = service.batch_get_values(
        SheetsBatchGetRequest(
            spreadsheet_id="fixture-book", ranges=["First!A1:B2", "Empty!A1"]
        )
    )
    assert result.success
    assert isinstance(result.content, SheetsBatchGetResponse)
    assert [item.range for item in result.content.value_ranges] == [
        "First!A1:B2",
        "Empty!A1",
    ]
    assert result.content.value_ranges[0].values == [[1, True]]
    assert result.content.value_ranges[1].values == []
    resource.batchGet.assert_called_once_with(
        spreadsheetId="fixture-book",
        ranges=["First!A1:B2", "Empty!A1"],
        majorDimension="ROWS",
        valueRenderOption="FORMATTED_VALUE",
        dateTimeRenderOption="SERIAL_NUMBER",
    )
    resource.batchGet.return_value.execute.assert_called_once_with(num_retries=0)


def test_columns_formula_and_date_options_are_explicit(wired):
    service, resource = wired
    resource.batchGet.return_value.execute.return_value = {
        "spreadsheetId": "fixture-book",
        "valueRanges": [
            {"range": "Sheet1!A1", "majorDimension": "COLUMNS", "values": [["=1+1"]]}
        ],
    }
    result = service.batch_get_values(
        SheetsBatchGetRequest(
            spreadsheet_id="fixture-book",
            ranges=["Sheet1!A1"],
            major_dimension="COLUMNS",
            value_render_option="FORMULA",
            date_time_render_option="FORMATTED_STRING",
        )
    )
    assert result.success
    assert resource.batchGet.call_args.kwargs["majorDimension"] == "COLUMNS"
    assert resource.batchGet.call_args.kwargs["valueRenderOption"] == "FORMULA"
    assert (
        resource.batchGet.call_args.kwargs["dateTimeRenderOption"] == "FORMATTED_STRING"
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"spreadsheet_id": " "},
        {"spreadsheet_id": 123},
        {"ranges": []},
        {"ranges": [" "]},
        {"ranges": [1]},
        {"ranges": ["A1"] * 101},
        {"major_dimension": "cells"},
        {"value_render_option": "RAW"},
        {"date_time_render_option": "iso"},
        {"unexpected": True},
    ],
)
def test_invalid_request_refused_by_closed_model(overrides):
    with pytest.raises(ValidationError):
        SheetsBatchGetRequest.model_validate(
            {"spreadsheet_id": "fixture-book", "ranges": ["A1"], **overrides}
        )


def test_mutated_request_is_revalidated_before_sdk_call(wired):
    service, resource = wired
    request = SheetsBatchGetRequest(spreadsheet_id="fixture-book", ranges=["A1"])
    request.ranges.clear()
    result = service.batch_get_values(request)
    assert not result.success
    resource.batchGet.assert_not_called()


def test_model_construct_does_not_bypass_validation(wired):
    service, resource = wired
    request = SheetsBatchGetRequest.model_construct(
        spreadsheet_id="fixture-book", ranges=[]
    )
    assert not service.batch_get_values(request).success
    resource.batchGet.assert_not_called()


def test_legacy_construction_never_discovers_auth_for_new_operation():
    with (
        patch("googleapiclient.discovery.build") as build,
        patch.object(GoogleSheetsService, "initialize") as initialize,
        patch.object(GoogleSheetsService, "_initialize_config") as config,
    ):
        result = GoogleSheetsService().batch_get_values(
            SheetsBatchGetRequest(spreadsheet_id="fixture-book", ranges=["A1"])
        )
    assert not result.success
    build.assert_not_called()
    initialize.assert_not_called()
    config.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {"spreadsheetId": "wrong-book", "valueRanges": [{"range": "A1"}]},
        {"spreadsheetId": "fixture-book", "valueRanges": []},
        {"spreadsheetId": "fixture-book", "valueRanges": [{"range": "A1"}]},
        {
            "spreadsheetId": "fixture-book",
            "valueRanges": [
                {"range": "A1", "majorDimension": "COLUMNS"},
                {"range": "B1"},
            ],
        },
        {"spreadsheetId": "fixture-book", "valueRanges": "inert-private-value"},
        {
            "spreadsheetId": "fixture-book",
            "valueRanges": [
                {"range": "A1", "values": [[{"inert-private-value": 1}]]},
                {"range": "B1"},
            ],
        },
        {
            "spreadsheetId": "fixture-book",
            "valueRanges": [{"range": "A1"}, {"range": "B1"}],
            "unknown": "inert-private-value",
        },
    ],
)
def test_wrong_book_partial_or_malformed_data_is_not_returned(wired, payload, caplog):
    service, resource = wired
    resource.batchGet.return_value.execute.return_value = deepcopy(payload)
    result = service.batch_get_values(
        SheetsBatchGetRequest(spreadsheet_id="fixture-book", ranges=["A1", "B1"])
    )
    assert not result.success
    assert "inert-private-value" not in str(result.error)
    assert "inert-private-value" not in caplog.text
    resource.batchGet.return_value.execute.assert_called_once_with(num_retries=0)


def test_sdk_exception_is_sanitized_and_never_retried(wired, caplog):
    service, resource = wired
    resource.batchGet.return_value.execute.side_effect = RuntimeError("inert-secret")
    result = service.batch_get_values(
        SheetsBatchGetRequest(spreadsheet_id="fixture-book", ranges=["A1"])
    )
    assert not result.success
    assert "inert-secret" not in str(result.error)
    assert "inert-secret" not in caplog.text
    resource.batchGet.assert_called_once()
    resource.batchGet.return_value.execute.assert_called_once_with(num_retries=0)


@pytest.mark.parametrize("cell", [float("nan"), float("inf"), {"invalid": 1}, [1]])
def test_non_scalar_or_nonfinite_cells_are_refused(cell):
    with pytest.raises(ValidationError):
        SheetsValueRange(range="A1", values=[[cell]])


def test_client_cell_limit_applies_across_ranges():
    ranges = [
        {"range": "A1", "values": [[0] * 60_000]},
        {"range": "B1", "values": [[0] * 60_000]},
    ]
    with pytest.raises(ValidationError):
        SheetsBatchGetResponse.model_validate(
            {"spreadsheetId": "fixture-book", "valueRanges": ranges}
        )


def test_duplicate_requested_ranges_are_preserved(wired):
    service, resource = wired
    resource.batchGet.return_value.execute.return_value = {
        "spreadsheetId": "fixture-book",
        "valueRanges": [{"range": "A1"}, {"range": "A1"}],
    }
    result = service.batch_get_values(
        SheetsBatchGetRequest(spreadsheet_id="fixture-book", ranges=["A1", "A1"])
    )
    assert result.success
    assert len(result.content.value_ranges) == 2
    assert resource.batchGet.call_args.kwargs["ranges"] == ["A1", "A1"]
