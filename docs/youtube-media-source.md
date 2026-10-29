# YouTube publish: where the bytes come from

A job names its video (and thumbnail and captions) in one of two ways, never both:

- **`path`** (with `mtime_ms` for the video): a file on the device, as before.
- **`object`**: `{"store": "staging", "key": "episodes/take-1.mp4", "version": "v1"}`, one
  version of an object in a staging store. The job names no address and holds no
  credential. The caller of the executor passes an `object_reader` that turns the store
  label into range reads (`ObjectReader.stat` and `.read`); without one, a job that
  names an object is held as `no_object_store`.

Either way the transfer reads ranges, so the resume rules above are the same. Before the
first byte the executor checks the source against the job:

- When the store keeps the sha256 the studio recorded, it must equal the job's. A
  difference holds the job as `file_changed` before any byte is read.
- The executor then reads the whole source once and compares its sha256 with the job's.
  A mismatch holds the job as `file_changed`, and nothing is uploaded.
- While sending, an object whose version or size no longer matches stops the transfer
  the way a changed local file does.

This page covers only the media source. The rest of the YouTube publish flow (sessions, resumable
transfer, relay, 30-day retention) is described in the package docstrings of
`src/zeo_integrations/google/youtube/`.

Source: zeroemployeeorg/zeocore commit d689e6d0e7a66a74500b1b32d2eaf31d9c2cadfe, docs/integrations/youtube.md (blob c4a938355d5bf5e26a68ca2312582fbd458700a7),
section "Where the bytes come from" only. MIT, Copyright (c) 2026 Rod Rivera.
