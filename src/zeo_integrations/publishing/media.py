"""Local immutable media staging and bounded inspection. MIT, Copyright 2026 ZEO.

Media staging never downloads remote inputs. Uploads use an injected transport;
the host binds approved content-addressed bytes to provider upload destinations.
"""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .workflow import Asset, WorkflowError


def sniff(header: bytes) -> str:
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header[:6] in {b"GIF87a", b"GIF89a"}:
        return "image/gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    if header[4:8] == b"ftyp" and header[8:12] in {
        b"isom",
        b"iso2",
        b"mp41",
        b"mp42",
        b"avc1",
        b"M4V ",
    }:
        return "video/mp4"
    if header.startswith(b"%PDF-"):
        return "application/pdf"
    raise WorkflowError("unsupported media signature")


class MediaLibrary:
    """Caller-owned durable directory; never deletes source or staged media."""

    def __init__(self, directory):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def stage(
        self, source, *, asset_id: str, alt_text: str = "", max_bytes=2_147_483_648
    ):
        if not 0 < max_bytes <= 2_147_483_648:
            raise WorkflowError("media size bound")
        source = Path(source)
        if not source.is_file():
            raise WorkflowError("regular media file required")
        digest, size = hashlib.sha256(), 0
        temporary = None
        try:
            with (
                source.open("rb") as incoming,
                tempfile.NamedTemporaryFile(
                    dir=self.root, prefix=".stage-", delete=False
                ) as outgoing,
            ):
                temporary = Path(outgoing.name)
                header = incoming.read(64)
                media_type = sniff(header)
                chunk = header
                while chunk:
                    size += len(chunk)
                    if size > max_bytes:
                        raise WorkflowError("media exceeds size bound")
                    digest.update(chunk)
                    outgoing.write(chunk)
                    chunk = incoming.read(1024 * 1024)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            asset = Asset(
                asset_id=asset_id,
                sha256=digest.hexdigest(),
                media_type=media_type,
                size_bytes=size,
                alt_text=alt_text,
            )
            destination = self.root / asset.sha256
            try:
                os.link(temporary, destination)
                os.chmod(destination, 0o400)
            except FileExistsError:
                pass
            self.verify(asset)
            return asset
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def verify(self, asset: Asset) -> Path:
        asset = Asset.model_validate(asset.model_dump())
        path = self.root / asset.sha256
        if path.is_symlink() or not path.is_file():
            raise WorkflowError("media unavailable")
        digest, size = hashlib.sha256(), 0
        with path.open("rb") as stream:
            if sniff(stream.read(64)) != asset.media_type:
                raise WorkflowError("media type changed")
            stream.seek(0)
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                if size > asset.size_bytes:
                    raise WorkflowError("media changed")
                digest.update(chunk)
        if size != asset.size_bytes or digest.hexdigest() != asset.sha256:
            raise WorkflowError("media changed")
        return path

    def inspect(self, asset: Asset):
        """Probe local image/video codecs and geometry; PDF stays opaque.

        ffprobe is optional. It is restricted to the file protocol, bounded by
        a wall timeout and an output cap, and never receives a URL or shell text.
        """
        path = self.verify(asset)
        if asset.media_type == "application/pdf":
            return {"media_type": asset.media_type, "size_bytes": asset.size_bytes}
        binary = shutil.which("ffprobe")
        if binary is None:
            raise WorkflowError("ffprobe required for media inspection")
        failed = False
        try:
            # JSON is small with explicit fields; redirect diagnostics away from logs.
            command = [
                binary,
                "-v",
                "error",
                "-protocol_whitelist",
                "file",
                "-show_entries",
                "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
                "-of",
                "json",
                str(path),
            ]
            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env={"PATH": os.defpath},
            ) as process:
                deadline, output = time.monotonic() + 15, bytearray()
                try:
                    with selectors.DefaultSelector() as selector:
                        selector.register(process.stdout, selectors.EVENT_READ)
                        while True:
                            remaining = deadline - time.monotonic()
                            if remaining <= 0 or not selector.select(remaining):
                                raise WorkflowError("media probe timeout")
                            chunk = os.read(
                                process.stdout.fileno(), 65537 - len(output)
                            )
                            if not chunk:
                                break
                            output.extend(chunk)
                            if len(output) > 65536:
                                raise WorkflowError("media probe response too large")
                    if (
                        process.wait(timeout=max(0.01, deadline - time.monotonic()))
                        != 0
                    ):
                        raise WorkflowError("media probe failed")
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
            data = json.loads(output)
            video = next(s for s in data["streams"] if s["codec_type"] == "video")
            info = {
                "media_type": asset.media_type,
                "size_bytes": asset.size_bytes,
                "width": video["width"],
                "height": video["height"],
                "codec": video["codec_name"],
                "duration": float(data.get("format", {}).get("duration", 0)),
            }
            if info["width"] <= 0 or info["height"] <= 0:
                raise WorkflowError("media geometry")
            return info
        except Exception:
            failed = True
        if failed:
            raise WorkflowError("media inspection failed")

    def convert(self, asset: Asset, *, asset_id: str, profile: str):
        """Explicit derivative; original remains intact and approval must be renewed.

        square_jpeg pads to 1080 square; portrait_mp4 pads to 1080x1920,
        H.264/AAC, 30fps. No cropping or duration trimming is implicit.
        Run untrusted media processing in a host-managed resource sandbox.
        """
        if profile not in {"square_jpeg", "portrait_mp4"}:
            raise WorkflowError("unknown conversion profile")
        if profile == "square_jpeg" and asset.media_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise WorkflowError("still image required")
        if profile == "portrait_mp4" and asset.media_type != "video/mp4":
            raise WorkflowError("MP4 required")
        path = self.verify(asset)
        original = self.inspect(asset)
        binary = shutil.which("ffmpeg")
        if binary is None:
            raise WorkflowError("ffmpeg required for explicit conversion")
        suffix = ".jpg" if profile == "square_jpeg" else ".mp4"
        with tempfile.TemporaryDirectory(dir=self.root, prefix=".convert-") as folder:
            output = Path(folder) / ("derived" + suffix)
            command = [
                binary,
                "-v",
                "error",
                "-nostdin",
                "-protocol_whitelist",
                "file",
                "-i",
                str(path),
                "-map_metadata",
                "-1",
                "-threads",
                "2",
            ]
            if profile == "square_jpeg":
                command += [
                    "-vf",
                    "scale=1080:1080:force_original_aspect_ratio=decrease,"
                    "pad=1080:1080:(ow-iw)/2:(oh-ih)/2:white,setsar=1",
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    "-f",
                    "image2",
                ]
            else:
                command += [
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0?",
                    "-vf",
                    "scale=1080:1920:force_original_aspect_ratio=decrease:"
                    "force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                    "setsar=1",
                    "-r",
                    "30",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-movflags",
                    "+faststart",
                ]
            command += ["-fs", "2147483648", str(output)]
            failed = False
            try:
                subprocess.run(
                    command,
                    check=True,
                    timeout=300,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env={"PATH": os.defpath},
                )
            except (OSError, subprocess.SubprocessError):
                failed = True
            if failed:
                raise WorkflowError("media conversion failed")
            # Inspect in a temporary library before admitting any derivative.
            temporary = MediaLibrary(Path(folder) / "verify")
            derivative = temporary.stage(
                output, asset_id=asset_id, alt_text=asset.alt_text
            )
            info = temporary.inspect(derivative)
            if profile == "portrait_mp4" and (
                info["codec"] != "h264"
                or original["duration"] <= 0
                or abs(info["duration"] - original["duration"]) > 0.2
            ):
                raise WorkflowError("conversion incomplete or duration changed")
            return self.stage(output, asset_id=asset_id, alt_text=asset.alt_text)

    def resolver(self, url_for):
        """Bind approved digest to a host-owned immutable serving/upload route.

        url_for receives verified Asset and local path. It must return a stable
        HTTPS URL for those bytes, never a mutable source upload or credential.
        """
        from zeo_integrations._http.runtime import _url

        def resolve(asset):
            path = self.verify(asset)
            url = url_for(asset, path)
            _url(url)
            return url

        return resolve


class MediaUploader:
    """One explicitly admitted PUT of verified bytes to a host-bound upload URL.

    The caller must bind URL, account, digest and provider upload ID in Connect's
    durable claim. Injected transport owns auth, DNS policy and no-retry behavior.
    This does not add an arbitrary-URL operation to the Broker.
    """

    def __init__(self, transport, *, allowed_origins):
        import httpx

        from zeo_integrations._http.runtime import _url

        if not isinstance(transport, httpx.BaseTransport):
            raise WorkflowError("explicit upload transport required")
        if not allowed_origins or any(_url(o) != o for o in allowed_origins):
            raise WorkflowError("upload origins required")
        self.origins = frozenset(allowed_origins)
        self.http = httpx.Client(
            transport=transport, trust_env=False, follow_redirects=False
        )

    def close(self):
        self.http.close()

    def upload(
        self, library: MediaLibrary, asset: Asset, *, url: str, allow_effect=False
    ):
        import time

        import httpx

        from zeo_integrations._http import IntegrationError
        from zeo_integrations._http.runtime import _url

        if allow_effect is not True:
            raise IntegrationError("EFFECT_ADMISSION_REQUIRED")
        if _url(url) not in self.origins:
            raise IntegrationError("UPLOAD_ORIGIN")
        path = library.verify(asset)
        deadline = time.monotonic() + 300

        def chunks():
            digest, size = hashlib.sha256(), 0
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    if time.monotonic() >= deadline:
                        raise WorkflowError("upload deadline")
                    size += len(chunk)
                    if size > asset.size_bytes:
                        raise WorkflowError("media changed")
                    digest.update(chunk)
                    yield chunk
            if digest.hexdigest() != asset.sha256 or size != asset.size_bytes:
                raise WorkflowError("media changed")

        failed = False
        try:
            request = httpx.Request(
                "PUT",
                url,
                content=chunks(),
                headers={
                    "Content-Type": asset.media_type,
                    "Content-Length": str(asset.size_bytes),
                    "Accept-Encoding": "identity",
                },
                extensions={"timeout": httpx.Timeout(60).as_dict()},
            )
            response = self.http.send(request, stream=True, follow_redirects=False)
            try:
                if not 200 <= response.status_code < 300 or response.url != request.url:
                    raise WorkflowError("upload unconfirmed")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise WorkflowError("upload response encoding")
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > 65536 or time.monotonic() >= deadline:
                        raise WorkflowError("upload response bound")
                if time.monotonic() >= deadline:
                    raise WorkflowError("upload deadline")
                return {
                    "uploaded": True,
                    "sha256": asset.sha256,
                    "size_bytes": asset.size_bytes,
                }
            finally:
                response.close()
                self.http.cookies.clear()
        except Exception:
            failed = True
        if failed:
            raise IntegrationError("UPLOAD_UNCONFIRMED", outcome_unknown=True)
