"""M1: zeocore never imports zeo_integrations at import time.

zeo-integrations depends on zeocore (the langchain-community direction), never the
reverse. A fresh interpreter imports Core's public entry points and the integration
loader; none of that may pull in the aggregate.
"""

from __future__ import annotations

import subprocess
import sys

PROGRAM = """
import importlib, sys
for name in (
    "zeo_core",
    "zeo_core.cli",
    "zeo_core.integrations",
    "zeo_core.integrations.core",
    "zeo_core.integrations.loader",
):
    try:
        importlib.import_module(name)
    except ImportError:
        pass
leaked = sorted(m for m in sys.modules if m == "zeo_integrations" or m.startswith("zeo_integrations."))
print("\\n".join(leaked))
"""


def test_importing_zeocore_does_not_import_zeo_integrations() -> None:
    done = subprocess.run(  # noqa: S603 -- fixed program, no shell
        [sys.executable, "-c", PROGRAM],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert done.stdout.strip() == ""
