"""Explicit one-call X media lifecycle steps. Host owns bytes, identity and state.

Copyright2026 Zero Employee Organizations. SPDX-License-Identifier: MIT
"""

import hashlib
import re
from typing import Literal

from pydantic import Field

from zeo_integrations._http import IntegrationError

from . import Input, PublishingResponseError, XPublisher, _x_id, _x_outbound_id


class XMediaUpload(Input):
    media_type: Literal[
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/pjpeg",
        "image/tiff",
        "image/gif",
        "video/mp4",
        "video/webm",
        "video/mp2t",
        "video/quicktime",
    ]
    media_category: Literal["tweet_image", "tweet_gif", "tweet_video"]
    total_bytes: int = Field(ge=1, le=17179869184)


def _integer(value, *, effect):
    if type(value) is not int or not 0 <= value <= 2147483647:
        raise IntegrationError("MEDIA_RECEIPT", outcome_unknown=effect)
    return value


class _MediaCalls(XPublisher):
    def _failure(self, response, *, effect):
        error = super()._failure(response, effect=effect)
        # A no-post rejection does not prove no media mutation or partial chunk.
        return PublishingResponseError(
            http_status=error.http_status,
            provider_code=error.provider_code,
            provider_subcode=error.provider_subcode,
            retry_after=error.retry_after,
            definite_refusal=error.definite_refusal and not effect,
            effect=effect,
        )


class XMediaClient:
    """No file reads, implicit upload loop, retries, credentials or grants."""

    def __init__(self, transport, *, account_id):
        self._client = _MediaCalls(transport, account_id=account_id)

    def _receipt(self, document, *, effect, expected_id=None):
        data = self._client._data(document, effect=effect)
        media_id = _x_id(data.get("id"), effect=effect)
        if expected_id is not None and media_id != expected_id:
            raise IntegrationError("MEDIA_IDENTITY", outcome_unknown=effect)
        key = data.get("media_key")
        if (
            not isinstance(key, str)
            or re.fullmatch(r"[0-9]{1,3}_[0-9]{1,20}", key) is None
            or key.rsplit("_", 1)[1] != media_id
        ):
            raise IntegrationError("MEDIA_RECEIPT", outcome_unknown=effect)
        ttl = _integer(data.get("expires_after_secs"), effect=effect)
        return data, {"media_id": media_id, "media_key": key, "expires_after_secs": ttl}

    def initialize_upload(self, upload: XMediaUpload, *, key, allow_effect=False):
        upload = XMediaUpload.model_validate(upload.model_dump())
        expected = (
            "tweet_gif"
            if upload.media_type == "image/gif"
            else (
                "tweet_video"
                if upload.media_type.startswith("video/")
                else "tweet_image"
            )
        )
        if upload.media_category != expected:
            raise IntegrationError("MEDIA_CATEGORY")
        document, _ = self._client._call(
            "initialize_media_upload",
            "/2/media/upload/initialize",
            key=key,
            effect=True,
            admitted=allow_effect,
            expected_status=200,
            body=upload.model_dump(),
        )
        _, result = self._receipt(document, effect=True)
        result["stage"] = (
            "expired" if not result["expires_after_secs"] else "awaiting_upload"
        )
        return result

    def finalize_upload(self, media_id, *, key, allow_effect=False):
        media_id = _x_outbound_id(media_id)
        document, _ = self._client._call(
            "finalize_media_upload",
            "/2/media/upload/" + media_id + "/finalize",
            key=key,
            effect=True,
            admitted=allow_effect,
            expected_status=200,
        )
        return self._processing(document, media_id, effect=True, finalized=True)

    def append_chunk(self, media_id, segment_index, chunk, *, key, allow_effect=False):
        """One bounded segment. A lost answer requires abandoning the upload."""
        media_id = _x_outbound_id(media_id)
        if type(segment_index) is not int or not 0 <= segment_index <= 9999:
            raise IntegrationError("MEDIA_SEGMENT")
        if type(chunk) is not bytes or not 1 <= len(chunk) <= 524288:
            raise IntegrationError("MEDIA_CHUNK")
        digest = hashlib.sha256(chunk).hexdigest()
        boundary = "zeo-x-" + digest
        if boundary.encode("ascii") in chunk:
            raise IntegrationError("MEDIA_BOUNDARY")
        body = (
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="segment_index"\r\n\r\n'
                f"{segment_index}\r\n--{boundary}\r\n"
                'Content-Disposition: form-data; name="media"; '
                'filename="chunk.bin"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode("ascii")
            + chunk
            + f"\r\n--{boundary}--\r\n".encode("ascii")
        )
        document, _ = self._client._call(
            "append_media_upload",
            "/2/media/upload/" + media_id + "/append",
            key=key,
            effect=True,
            admitted=allow_effect,
            expected_status=200,
            raw_body=body,
            headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        )
        data = self._client._data(document, effect=True)
        expires = data.get("expires_at")
        if type(expires) is not int or not 0 <= expires <= 18446744073709551615:
            raise IntegrationError("MEDIA_RECEIPT", outcome_unknown=True)
        return {
            "media_id": media_id,
            "segment_index": segment_index,
            "chunk_sha256": digest,
            "expires_at": expires,
            "stage": "chunk_accepted",
        }

    def upload_status(self, media_id, *, key):
        media_id = _x_outbound_id(media_id)
        document, _ = self._client._call(
            "media_upload_status",
            "/2/media/upload",
            key=key,
            effect=False,
            method="GET",
            query={"command": "STATUS", "media_id": media_id},
            expected_status=200,
        )
        return self._processing(document, media_id, effect=False, finalized=False)

    def _processing(self, document, media_id, *, effect, finalized):
        data, result = self._receipt(document, effect=effect, expected_id=media_id)
        info = data.get("processing_info")
        state = None
        if "processing_info" in data:
            if (
                not isinstance(info, dict)
                or not isinstance(info.get("state"), str)
                or info["state"]
                not in {"pending", "in_progress", "succeeded", "failed"}
            ):
                raise IntegrationError("MEDIA_STATE", outcome_unknown=effect)
            state = info["state"]
            for name in ("check_after_secs", "progress_percent"):
                if name in info:
                    result[name] = _integer(info[name], effect=effect)
            if result.get("progress_percent", 0) > 100:
                raise IntegrationError("MEDIA_STATE", outcome_unknown=effect)
        stage = {
            "pending": "processing",
            "in_progress": "processing",
            "succeeded": "ready",
            "failed": "failed",
        }.get(state)
        if stage is None:
            stage = "ready" if finalized else "processing_state_absent"
        result.update(
            provider_state=state,
            stage="expired" if not result["expires_after_secs"] else stage,
        )
        return result
