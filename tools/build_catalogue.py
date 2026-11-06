"""Build SDK-free catalogue from the bounded HTTP adapters; no network calls."""

import importlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "src/zeo_integrations"
entries = {}
for path in sorted(root.glob("*/__init__.py")):
    if "class Client(" not in path.read_text():
        continue
    client = importlib.import_module("zeo_integrations." + path.parent.name).Client
    operations = {}
    for operation in client.operations:
        operations[operation] = {
            "input_schema": client.input_model(operation).model_json_schema(),
            "effect_policy": (
                "GET/HEAD read; other HTTP methods need effect admission"
            ),
        }
    entries[client.provider] = {
        "module": client.__module__,
        "origins": list(client.origins),
        "operations": operations,
    }
(root / "catalogue.json").write_text(json.dumps(entries, indent=2) + "\n")
print(
    f"{len(entries)} providers, "
    f"{sum(len(p['operations']) for p in entries.values())} operations"
)
