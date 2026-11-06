"""Lazy catalogue: listing never imports a provider or SDK."""

from __future__ import annotations

import importlib
import json
from importlib.resources import files


def providers() -> dict:
    return json.loads(files("zeo_integrations").joinpath("catalogue.json").read_text())


def load(provider: str):
    entries = providers()
    if provider not in entries:
        raise ValueError("unknown provider")
    return importlib.import_module(entries[provider]["module"]).Client


def coverage() -> list[dict]:
    """All requested rows, including explicit holds and implementation limits."""
    return json.loads(files("zeo_integrations").joinpath("coverage.json").read_text())


def metadata(provider: str) -> dict:
    """Provider auth/discovery metadata; never a grant or admission decision."""
    return json.loads(
        files("zeo_integrations").joinpath("provider_metadata.json").read_text()
    )[provider]
