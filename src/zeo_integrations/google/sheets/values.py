"""Typed, bounded data for the Sheets v4 multi-range read operation.

Contract: https://developers.google.com/workspace/sheets/api/reference/rest/v4/
spreadsheets.values/batchGet. Limits are local client policies, not API quotas.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Dimension = Literal["ROWS", "COLUMNS"]
ValueRenderOption = Literal["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
DateTimeRenderOption = Literal["SERIAL_NUMBER", "FORMATTED_STRING"]
CellValue = str | bool | int | float | None
RangeName = Annotated[str, Field(min_length=1, max_length=4096)]


class _ValuesModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        populate_by_name=True,
        allow_inf_nan=False,
        str_max_length=50_000,
    )


class SheetsBatchGetRequest(_ValuesModel):
    """Read up to 100 ranges, using only credentials supplied by the host."""

    spreadsheet_id: str = Field(min_length=1, max_length=256)
    ranges: list[RangeName] = Field(min_length=1, max_length=100)
    major_dimension: Dimension = "ROWS"
    value_render_option: ValueRenderOption = "FORMATTED_VALUE"
    date_time_render_option: DateTimeRenderOption = "SERIAL_NUMBER"

    @field_validator("spreadsheet_id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A spreadsheet ID is required")
        return value

    @field_validator("ranges")
    @classmethod
    def nonblank_ranges(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("Each range must be nonblank")
        return value


class SheetsValueRange(_ValuesModel):
    """One returned range; Google omits values for an empty range."""

    range: RangeName
    major_dimension: Dimension = Field(default="ROWS", alias="majorDimension")
    values: list[list[CellValue]] = Field(default_factory=list, max_length=10_000)

    @model_validator(mode="after")
    def bounded_cells(self) -> "SheetsValueRange":
        if sum(len(row) for row in self.values) > 100_000:
            raise ValueError("Range exceeds the client cell limit")
        return self


class SheetsBatchGetResponse(_ValuesModel):
    """Ordered ranges from one spreadsheet, validated before returning data."""

    spreadsheet_id: str = Field(alias="spreadsheetId", min_length=1, max_length=256)
    value_ranges: list[SheetsValueRange] = Field(
        alias="valueRanges", min_length=1, max_length=100
    )

    @model_validator(mode="after")
    def bounded_cells(self) -> "SheetsBatchGetResponse":
        if (
            sum(
                len(row)
                for value_range in self.value_ranges
                for row in value_range.values
            )
            > 100_000
        ):
            raise ValueError("Response exceeds the client cell limit")
        return self
