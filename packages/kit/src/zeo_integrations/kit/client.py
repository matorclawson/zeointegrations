# Copyright (c) 2026 Rod Rivera
# SPDX-License-Identifier: MIT
# Adapted from zeroemployeeorg/zeocore@25a9c899c17ac6cdf54f4949e54b0fcc800cce91
# Source: src/zeo_core/integrations/kit/client.py
# MIT permission notice retained in package LICENSE; provenance in NOTICE.
"""Current Kit API reads for retirement migration and audit only."""

from __future__ import annotations

from pydantic import SecretStr, TypeAdapter, ValidationError

from .models import (
    CustomField,
    Form,
    FormStatus,
    Page,
    PageRequest,
    ReadRecord,
    Subscriber,
    SubscriberStatus,
    Tag,
)
from .transport import KitAPIError, KitTransport

_DEFAULT_PAGE = PageRequest()


class KitClient:
    def __init__(
        self,
        api_key: SecretStr | None = None,
        *,
        access_token: SecretStr | None = None,
        transport: KitTransport | None = None,
    ) -> None:
        self._transport = transport or KitTransport(api_key, access_token=access_token)

    def close(self) -> None:
        self._transport.close()

    def _page(
        self,
        path: str,
        key: str,
        page: PageRequest,
        *,
        model: type[ReadRecord],
        params: dict[str, str | int | bool] | None = None,
    ) -> Page:
        if not isinstance(page, PageRequest):
            raise TypeError("page must be a PageRequest")
        query: dict[str, str | int | bool] = {
            "per_page": page.per_page,
            **(params or {}),
        }
        if page.after is not None:
            query["after"] = page.after
        data = self._transport.request("GET", path, params=query)
        rows, paging = data.get(key), data.get("pagination")
        if (
            not isinstance(rows, list)
            or len(rows) > page.per_page
            or not all(isinstance(row, dict) for row in rows)
            or not isinstance(paging, dict)
        ):
            raise KitAPIError("RESPONSE", "Kit returned an invalid page")
        has_next, has_previous = (
            paging.get("has_next_page"),
            paging.get("has_previous_page"),
        )
        if type(has_next) is not bool or type(has_previous) is not bool:
            raise KitAPIError("RESPONSE", "Kit omitted pagination completeness")
        after = paging.get("end_cursor") if has_next else None
        if has_next and (
            not isinstance(after, str)
            or not after
            or len(after) > 2048
            or after == page.after
        ):
            raise KitAPIError("RESPONSE", "Kit returned an invalid or repeated cursor")
        try:
            selected = [
                model.model_validate(row).model_dump(mode="json") for row in rows
            ]
        except ValidationError:
            raise KitAPIError("RESPONSE", "Kit returned invalid read data") from None
        identities = [row["id"] for row in selected]
        if len(set(identities)) != len(identities):
            raise KitAPIError("RESPONSE", "Kit returned duplicate resource identities")
        return Page(
            results=selected,
            next_after=after,
            complete=page.after is None and not has_next and not has_previous,
        )

    def list_subscribers(
        self, page: PageRequest = _DEFAULT_PAGE, *, status: SubscriberStatus = "all"
    ) -> Page:
        status = TypeAdapter(SubscriberStatus).validate_python(status)
        return self._page(
            "/v4/subscribers",
            "subscribers",
            page,
            model=Subscriber,
            params={"status": status, "slim": False},
        )

    def list_tags(self, page: PageRequest = _DEFAULT_PAGE) -> Page:
        return self._page("/v4/tags", "tags", page, model=Tag)

    def list_forms(
        self, page: PageRequest = _DEFAULT_PAGE, *, status: FormStatus = "all"
    ) -> Page:
        status = TypeAdapter(FormStatus).validate_python(status)
        return self._page(
            "/v4/forms", "forms", page, model=Form, params={"status": status}
        )

    def list_custom_fields(self, page: PageRequest = _DEFAULT_PAGE) -> Page:
        return self._page("/v4/custom_fields", "custom_fields", page, model=CustomField)
