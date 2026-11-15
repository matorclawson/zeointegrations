# Google Sheets with credentials held in memory

Install the aggregate with its Google SDK extra at an exact reviewed commit.
The host builds a google-auth credentials object from its own secret store and
passes it to `GoogleSheetsService.from_credentials(credentials)`. This additive
constructor bypasses file/configuration loading and browser authorization.
It uses the SDK's bundled static discovery document and disables discovery-cache
writes. It does not refresh credentials or make a provider request at construction.

```python
from zeo_integrations.google.sheets import GoogleSheetsService

# credentials is an already constructed google-auth Credentials object.
sheets = GoogleSheetsService.from_credentials(credentials)
result = sheets.get_values("SPREADSHEET_ID", "Sheet1!A1:B10")
if not result.success:
    raise RuntimeError("Sheet read failed")
rows = result.content

# RAW prevents text beginning with '=' from becoming a spreadsheet formula.
written = sheets.append_values(
    "SPREADSHEET_ID", "Sheet1!A1", [["item", "=literal text"]],
    value_input_option="RAW",
)
```

For a service account, the host may construct
`google.oauth2.service_account.Credentials.from_service_account_info(info,
scopes=GoogleSheetsService.SCOPES)` from an injected JSON object. For an OAuth
user, it may construct `google.oauth2.credentials.Credentials` from the injected
refresh token, client ID, client secret and Google's token endpoint. The host
validates this configuration and never prints or persists the credential object.
The library does not discover credentials from environment variables or files
through this constructor; passing `None` is refused rather than invoking default
authentication. Existing file-based constructor behavior remains available.

The host owns Google enrollment, the spreadsheet share/ACL, permitted ranges,
scopes, refresh-token custody and execution policy. A service account needs
access to the selected spreadsheet; OAuth user access follows that principal's
permissions. Requests may refresh credentials through google-auth when needed.
Read and append are synchronous SDK calls: use the host's bounded worker rather
than blocking an async conversation loop. Do not log provider exceptions,
credential objects or sheet contents. An append whose response is lost may have
succeeded; a failure does not authorize a blind retry. This constructor adds no
idempotency or reconciliation guarantee to the existing SDK operation methods.

Tests use a mocked discovery builder and inert credential objects; no live
Google request, browser flow or key file is needed.
