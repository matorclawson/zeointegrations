# Typed multi-range Sheets reads

`GoogleSheetsService.batch_get_values` adds a typed read without changing the
existing seven methods or the Core integration protocol. Construct the service
with `from_credentials` and pass a `SheetsBatchGetRequest`. File-based
construction cannot invoke this operation or trigger credential discovery.
The host owns scopes, credential refresh, the execution deadline and any
synchronous worker. A read-only Sheets scope suffices for this operation;
construction does not grant scopes or broaden existing credentials.

The request names one spreadsheet and up to 100 nonblank ranges. It selects
`ROWS` or `COLUMNS`, a value-render mode, and a date/time-render mode. Returned
`SheetsBatchGetResponse.value_ranges` retain the API response order, including
duplicate ranges. Empty ranges may omit `values`; those become empty lists.
The client refuses a different spreadsheet, an unexpected range count or
dimension, unknown fields, malformed cells, and nonfinite numbers. It does not
compare A1 range strings for equality: Google may return canonical sheet-qualified
ranges for shorter input notation.

The request executes once with SDK retries explicitly disabled. Provider and
validation exceptions become fixed errors that contain neither credentials nor
cell data. No write, automatic retry, auth enrollment, new dependency, Core
entry-point change or live-provider fixture is introduced.

Local policies cap requests at 100 ranges, response rows at 10,000 per range,
response cells at 100,000 total, range strings at 4,096 characters and cell
strings at 50,000 characters. These are client limits, not Google quotas.
Validation runs after SDK decoding and is not a transport byte limit. Request
models are revalidated before constructing an SDK request, including mutable
lists or models built without validation.

Official contracts:

- [spreadsheets.values.batchGet](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchGet)
- [ValueRange](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values#ValueRange)

Fresh offline tests cover operation options, order, duplicates, empty cells,
closed request/response validation, partial/mismatched results, bounded scalar
values, missing injected credentials and sanitized single-attempt failures.
They must run with the full repository qualification on the admitted build host
before publication. This source addition does not claim all Sheets operations
or complete parity with any reference service.
