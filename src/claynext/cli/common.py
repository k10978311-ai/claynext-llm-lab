"""Shared CLI helpers for the LLM lab."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def progress_printer(pct: int, msg: str = "") -> None:
    text = str(msg or "").strip()
    if text:
        print(f"[{int(pct):3d}%] {text}", file=sys.stderr, flush=True)
    else:
        print(f"[{int(pct):3d}%]", file=sys.stderr, flush=True)


def require_file(path: str | Path, *, label: str = "file") -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        die(f"{label} not found: {p}")
    return p


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def make_progress(quiet: bool) -> Callable[[int, str], None] | None:
    if quiet:
        return None
    return progress_printer
