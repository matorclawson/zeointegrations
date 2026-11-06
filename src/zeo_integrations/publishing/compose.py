"""Compile editorial variants into explicit, reviewable hosted-operation steps.

The host supplies operation IDs from its admitted Connect catalogue. No routes
are invented or enabled here. Unsupported formats fail before any draft approval.
"""

from zeo_core.integrations.hosted.client import HostedExpectedBinding

from .workflow import Asset, Step, Target, WorkflowError


def compose_target(
    *,
    target_id: str,
    platform: str,
    connection_id: str,
    expect: HostedExpectedBinding,
    caption: str,
    assets: list[Asset],
    operations: dict[str, str],
    mode="publish",
    privacy_level=None,
):
    steps = []

    def add(step_id, action, arguments, *, read=False, wait=None):
        if action not in operations:
            raise WorkflowError(f"operation unavailable: {platform}.{action}")
        steps.append(
            Step(
                step_id=step_id,
                operation_id=operations[action],
                arguments=arguments,
                kind="read" if read else "effect",
                **(wait or {}),
            )
        )

    def ref(step, field="container_id"):
        return {"$step": step, "field": field}

    def media(asset):
        return {"$asset": asset.asset_id}

    def ready(step_id, source):
        add(
            step_id,
            "container_status",
            {"container_id": ref(source)},
            read=True,
            wait={
                "wait_field": "provider_status",
                "ready_values": ["FINISHED"],
                "pending_values": ["IN_PROGRESS"],
                "max_polls": 60,
            },
        )

    if platform in {"instagram", "threads"}:
        formats = {"image/jpeg", "video/mp4"}
        if platform == "threads":
            formats.add("image/png")
        if len(assets) > 10 or any(a.media_type not in formats for a in assets):
            raise WorkflowError("unsupported Meta media; convert explicitly first")
        if platform == "instagram" and (not assets or len(caption) > 2200):
            raise WorkflowError("Instagram requires media and bounded caption")
        if platform == "threads" and (not caption or len(caption) > 500):
            raise WorkflowError("Threads caption required and bounded")
        if len(assets) > 1:
            for index, asset in enumerate(assets):
                step_id = f"item{index}"
                add(
                    step_id,
                    "create_carousel_item",
                    {
                        "item": {
                            "media_type": "VIDEO"
                            if asset.media_type.startswith("video/")
                            else "IMAGE",
                            "media_url": media(asset),
                            "alt_text": asset.alt_text,
                        }
                    },
                )
                ready(f"ready{index}", step_id)
            add(
                "container",
                "create_carousel",
                {
                    "carousel": {
                        "caption": caption,
                        "children": [ref(f"item{i}") for i in range(len(assets))],
                    }
                },
            )
        else:
            asset = assets[0] if assets else None
            if platform == "instagram":
                add(
                    "container",
                    "create_container",
                    {
                        "media": {
                            "media_type": "REELS"
                            if asset.media_type.startswith("video/")
                            else "IMAGE",
                            "media_url": media(asset),
                            "caption": caption,
                        }
                    },
                )
            else:
                add(
                    "container",
                    "create_container",
                    {
                        "post": {
                            "media_type": "TEXT"
                            if asset is None
                            else (
                                "VIDEO"
                                if asset.media_type.startswith("video/")
                                else "IMAGE"
                            ),
                            "text": caption,
                            "media_url": media(asset) if asset else None,
                        }
                    },
                )
        ready("ready", "container")
        add("publish", "publish_container", {"container_id": ref("container")})
    elif platform in {"x", "linkedin"}:
        if assets:
            raise WorkflowError("upload receipt workflow required for X/LinkedIn media")
        limit = 280 if platform == "x" else 3000
        if not caption or len(caption) > limit:
            raise WorkflowError("caption exceeds supported text format")
        add("publish", "publish", {"post": {"text": caption}})
    elif platform == "tiktok":
        if len(assets) != 1 or assets[0].media_type != "video/mp4":
            raise WorkflowError("TikTok requires one MP4")
        if mode == "inbox":
            add("upload", "upload_to_inbox", {"video": {"video_url": media(assets[0])}})
        elif mode == "publish" and privacy_level is not None:
            add(
                "upload",
                "publish_video",
                {
                    "post": {
                        "video_url": media(assets[0]),
                        "title": caption,
                        "privacy_level": privacy_level,
                        "disable_duet": True,
                        "disable_comment": True,
                        "disable_stitch": True,
                    }
                },
            )
        else:
            raise WorkflowError("explicit TikTok mode and privacy choice required")
        add(
            "status",
            "status",
            {"publish_id": ref("upload", "publish_id")},
            read=True,
            wait={
                "wait_field": "stage",
                "ready_values": ["inbox_delivered" if mode == "inbox" else "published"],
                "pending_values": ["processing"],
                "max_polls": 120,
            },
        )
    else:
        raise WorkflowError("platform requires its existing specialized workflow")
    return Target(
        target_id=target_id,
        platform=platform,
        connection_id=connection_id,
        expect=expect,
        caption=caption,
        asset_ids=[a.asset_id for a in assets],
        steps=steps,
        completion="inbox_delivered"
        if platform == "tiktok" and mode == "inbox"
        else "published",
    )
