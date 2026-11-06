"""Exception vocabulary only; no network functions."""

from types import SimpleNamespace

from .runtime import HTTPError, RequestException
from .runtime import _Response as Response

exceptions = SimpleNamespace(HTTPError=HTTPError, RequestException=RequestException)
__all__ = ["exceptions", "Response"]
