"""
Single-instance guard for the checkpointed experiment runners.

Two copies of the same run were once started by accident, and both wrote the same
checkpoint file. Each write is a whole-file rewrite, so that particular race produced a
superset rather than corruption, but only by luck: interleaving a write with a read would
have lost completed units, and the two processes duplicated hours of compute.

Usage:

    with single_instance("label_budget"):
        ...

A stale lock left by a crashed process is detected by checking whether the recorded PID is
still alive, and is reclaimed rather than requiring manual cleanup, since crash recovery is
exactly the situation these runners exist to survive.
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path

from src.config import RESULTS

LOCK_DIR = RESULTS / ".locks"


def _alive(pid: int) -> bool:
    """Is a process with this PID running? Windows and POSIX."""
    if os.name == "nt":
        import subprocess

        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, errors="replace").stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


class AlreadyRunning(RuntimeError):
    pass


@contextlib.contextmanager
def single_instance(name: str):
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock = LOCK_DIR / f"{name}.lock"

    if lock.exists():
        try:
            held = json.loads(lock.read_text(encoding="utf-8"))
            pid = int(held.get("pid", -1))
        except (json.JSONDecodeError, ValueError):
            pid = -1
        if pid > 0 and _alive(pid):
            raise AlreadyRunning(
                f"'{name}' is already running as PID {pid}. Two writers would duplicate "
                f"compute and race on the checkpoint. Stop it first, or delete {lock} if "
                f"you are certain it is dead."
            )
        print(f"reclaiming stale lock from dead PID {pid}")

    lock.write_text(json.dumps({"pid": os.getpid(), "name": name}), encoding="utf-8")
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()
