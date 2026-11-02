"""Fill Gemini candidates on spoken_train_next2.jsonl and let Jev rank them.

Reads only data/khmer_spoken/workspace/spoken_train_next2.jsonl.
Refuses any id from kp-1001 through kp-2000. Does not open spoken_scale.jsonl.
There is no --write-split flag. Does not approve rows, change licence, or start a trainer.

Resume:
    PYTHONPATH=src .venv/bin/python data/outputs/voice_training/2026-10-27-spoken-next2/fill_next2.py --limit 200 --max-minutes 90
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import time
import traceback
from pathlib import Path

from claynext.models.jev_decisions import jev_key_configured, rank_khmer_candidates
from claynext.models.khmer_spoken.providers.google_gemini_provider import GeminiTeacherProvider

ROOT = Path(__file__).resolve().parents[4]
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
OUT_DIR = Path(__file__).resolve().parent
PROGRESS = OUT_DIR / "fill_next2_progress.json"
SUMMARY = OUT_DIR / "fill_next2_run.json"
STATUS = OUT_DIR / "fill_next2_status.json"
PID_PATH = OUT_DIR / "fill_next2.pid"
ID_LO = 2201
ID_HI = 2400
HOLDOUT_LO = 1001
HOLDOUT_HI = 2000
FROZEN = (
    "review_status",
    "verified_by",
    "verified_at",
    "approved_text",
    "license_type",
    "license_notes",
    "reviewer_notes",
    "stub_khmer",
    "source_text",
)


def redact(text: str) -> str:
    cleaned = text or ""
    cleaned = re.sub(r"AIza[\w\-]+", "[redacted]", cleaned)
    cleaned = re.sub(r"sk-[A-Za-z0-9_\-]+", "[redacted]", cleaned)
    cleaned = re.sub(r"(?i)(key|token|secret|authorization)=([^\s&\"']+)", r"\1=[redacted]", cleaned)
    cleaned = re.sub(r"(?i)bearer\s+\S+", "bearer [redacted]", cleaned)
    cleaned = re.sub(r"https://\S+", "[redacted-url]", cleaned)
    return cleaned[:500]


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if isinstance(record.args, tuple):
            record.args = tuple(redact(str(item)) for item in record.args)
        elif record.args:
            record.args = redact(str(record.args))
        return True


def _install_redaction() -> None:
    logging.basicConfig(level=logging.WARNING)
    redactor = _RedactFilter()
    root = logging.getLogger()
    root.addFilter(redactor)
    for handler in root.handlers:
        handler.addFilter(redactor)


def kp_num(row_id: str) -> int:
    tail = str(row_id or "").split("-", 1)[-1]
    if not tail.isdigit():
        raise SystemExit(f"bad id {row_id}")
    return int(tail)


def _stop_class(message: str) -> str:
    text = (message or "").lower()
    if any(token in text for token in ("401", "403", "were rejected", "invalid api key")):
        return "auth"
    if any(token in text for token in (
        "cooling", "rate-limited", "rate limited", "503", "unavailable",
        "no available gemini", "high demand", "no response", "timed out", "timeout",
    )):
        return "cooldown"
    return ""


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _other_fill() -> str:
    """Return another Python fill process. Shells that mention the script do not count."""
    try:
        listed = subprocess.check_output(["ps", "-ax", "-o", "pid=,comm="], text=True)
    except (OSError, subprocess.CalledProcessError):
        return ""
    me = os.getpid()
    for line in listed.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid_text, comm = parts
        if not pid_text.isdigit() or int(pid_text) == me:
            continue
        if not Path(comm).name.lower().startswith("python"):
            continue
        try:
            args = subprocess.check_output(["ps", "-p", pid_text, "-o", "args="], text=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        if any(token in args for token in ("fill_scale.py", "fill_next.py", "fill_next2.py", "fill_kp")):
            return redact(f"{pid_text} {args.strip()}")
    return ""


def _empty(row: dict) -> bool:
    return not any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))


def _frozen(row: dict) -> tuple:
    return tuple(row.get(key) for key in FROZEN)


def _restore_frozen(row: dict, frozen: tuple) -> None:
    for key, value in zip(FROZEN, frozen, strict=True):
        row[key] = value


def _guard_rows(rows: list[dict]) -> None:
    ids = [row["id"] for row in rows]
    expected = [f"kp-{index}" for index in range(ID_LO, ID_HI + 1)]
    if ids != expected:
        raise SystemExit("train-next2 ids are not kp-2201 through kp-2400")
    if len(rows) > 200:
        raise SystemExit("refusing more than 200 rows")
    for row in rows:
        number = kp_num(row["id"])
        if HOLDOUT_LO <= number <= HOLDOUT_HI:
            raise SystemExit("refusing a holdout id")
        if row.get("review_status") != "pending_native_review":
            raise SystemExit(f"{row['id']} is not pending_native_review")
        if row.get("license_type") != "unknown":
            raise SystemExit(f"{row['id']} licence is not unknown")
        if row.get("verified_by") or row.get("approved_text"):
            raise SystemExit(f"{row['id']} looks approved")
        origin = row.get("origin")
        if origin not in {"synthetic", "gemini_teacher"}:
            raise SystemExit(f"{row['id']} origin is not a teacher draft")


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line if line.endswith("\n") else line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def _save(rows: list[dict]) -> None:
    _guard_rows(rows)
    _write_lines(WORKSPACE, [json.dumps(row, ensure_ascii=False) for row in rows])


def _attach(row: dict, teacher: GeminiTeacherProvider) -> tuple[bool, str]:
    frozen = _frozen(row)
    prior_origin = row.get("origin")
    prior = list(row.get("candidates") or [])
    try:
        result = teacher.generate_khmer_candidates(
            row["source_text"],
            source_lang=row.get("source_lang") or "en",
            emotion=row.get("emotion") or "neutral",
            register=row.get("register") or "neutral",
            speaker_id=row.get("speaker_id") or "",
            listener_id=row.get("listener_id") or "",
        )
    except Exception as exc:
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        return False, redact(f"{type(exc).__name__}: {exc}")
    if result.skipped or not result.ok:
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        return False, redact(result.error or "row_failed")
    new_cands = []
    for item in result.candidates:
        text = str((item or {}).get("text") or "").strip()
        if not text:
            continue
        new_cands.append({
            "text": text,
            "style": str(item.get("style") or "natural"),
            "provider": "gemini_teacher",
            "model": result.model,
            "notes": str(item.get("notes") or ""),
            "emotion": str(item.get("emotion") or row.get("emotion") or ""),
            "register": str(item.get("register") or row.get("register") or ""),
        })
    if not new_cands and result.text:
        new_cands.append({
            "text": result.text[:2000],
            "style": "natural",
            "provider": "gemini_teacher",
            "model": result.model,
            "notes": "raw_fallback",
            "emotion": row.get("emotion") or "",
            "register": row.get("register") or "",
        })
    if not new_cands:
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        return False, "no candidates parsed"
    row["candidates"] = prior + new_cands
    if prior_origin == "synthetic":
        row["origin"] = "gemini_teacher"
    if row.get("origin") not in {"synthetic", "gemini_teacher"} or _frozen(row) != frozen:
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        return False, "review fields changed; row reverted"
    return True, ""


def _rank_one(row: dict) -> str:
    if _empty(row):
        return "empty"
    frozen = _frozen(row)
    prior_origin = row.get("origin")
    meta = row.setdefault("metadata", {})
    if (meta.get("jev") or {}).get("applied"):
        return "already"
    prior = json.loads(json.dumps(row.get("candidates") or []))
    prior_jev = meta.get("jev")
    try:
        from claynext.models.khmer_spoken.schema import DialogueExample

        example = DialogueExample.from_dict(row)
        result = rank_khmer_candidates(example)
    except Exception:
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        if prior_jev is None:
            meta.pop("jev", None)
        else:
            meta["jev"] = prior_jev
        return "error"
    if not result.get("applied"):
        row["candidates"] = prior
        row["origin"] = prior_origin
        _restore_frozen(row, frozen)
        if prior_jev is None:
            meta.pop("jev", None)
        else:
            meta["jev"] = prior_jev
        return str(result.get("reason") or "not_applied")
    row["candidates"] = prior
    row["origin"] = prior_origin
    _restore_frozen(row, frozen)
    meta["jev"] = dict(example.metadata.get("jev") or result)
    if not meta["jev"].get("applied"):
        meta.pop("jev", None)
        return "not_applied"
    if _frozen(row) != frozen or row.get("review_status") != "pending_native_review":
        row["candidates"] = prior
        _restore_frozen(row, frozen)
        meta.pop("jev", None)
        return "review_changed"
    return "applied"


def _status(rows: list[dict], *, filled: int, last_id: str, stop_reason: str, jev_ranked: int) -> None:
    empty = [row["id"] for row in rows if _empty(row)]
    payload = {
        "source_rows": len(rows),
        "with_candidates": sum(1 for row in rows if not _empty(row)),
        "jev_ranked_rows": sum(1 for row in rows if (row.get("metadata") or {}).get("jev", {}).get("applied")),
        "filled_this_process": filled,
        "jev_ranked_this_process": jev_ranked,
        "last_id": last_id,
        "next_id": empty[0] if empty else "",
        "still_empty": len(empty),
        "stop_reason": stop_reason,
        "weights_written": False,
        "training_started": False,
        "promotion": "not_promoted",
        "licence": "unknown",
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "gemini_role": "teacher",
        "jev_role": "ranker",
        "weight_update": False,
        "workspace": "data/khmer_spoken/workspace/spoken_train_next2.jsonl",
        "holdout_ids_read": False,
        "write_split": False,
        "id_first": "kp-2201",
        "id_last": "kp-2400",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    STATUS.write_text(text, encoding="utf-8")
    SUMMARY.write_text(text, encoding="utf-8")
    PROGRESS.write_text(json.dumps({**payload, "stopped": bool(stop_reason)}, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    _install_redaction()
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--max-minutes", type=float, default=90)
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    other = _other_fill()
    if other:
        raise SystemExit(f"another fill is running: {other}")
    if PID_PATH.is_file():
        try:
            old = int(PID_PATH.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            old = 0
        if old and old != os.getpid() and _alive(old):
            raise SystemExit(f"fill_next2 already running pid {old}")
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    try:
        return _run(args)
    finally:
        if PID_PATH.is_file():
            try:
                current = int(PID_PATH.read_text(encoding="utf-8").strip() or "0")
            except ValueError:
                current = 0
            if current == os.getpid():
                PID_PATH.unlink(missing_ok=True)


def _run(args: argparse.Namespace) -> int:
    if WORKSPACE.name != "spoken_train_next2.jsonl" or "spoken_scale.jsonl" in str(WORKSPACE):
        raise SystemExit("refusing to fill any file except spoken_train_next2.jsonl")
    if not WORKSPACE.is_file():
        raise SystemExit(f"missing {WORKSPACE.name}")
    rows = [json.loads(line) for line in WORKSPACE.read_text(encoding="utf-8").splitlines() if line.strip()]
    _guard_rows(rows)
    todo = [row for row in rows if _empty(row)]
    limit = min(max(0, args.limit), len(todo), 200)
    batch = todo[:limit]
    deadline = time.monotonic() + max(1.0, args.max_minutes) * 60.0
    teacher = GeminiTeacherProvider(models=("gemini-flash-latest",))
    print(
        f"FILL empty={len(todo)} batch={len(batch)} gemini_available={teacher.available()} "
        f"jev={jev_key_configured()} max_minutes={args.max_minutes}",
        flush=True,
    )
    filled: list[str] = []
    jev_ranked = 0
    stop_reason = ""
    if not teacher.available():
        stop_reason = "missing_key"
    else:
        for index, row in enumerate(batch, start=1):
            if time.monotonic() >= deadline:
                stop_reason = "time_budget"
                print(f"ROW {row['id']} STOP time_budget", flush=True)
                break
            ok, err = _attach(row, teacher)
            if not ok:
                kind = _stop_class(err)
                if kind in {"auth", "cooldown"}:
                    stop_reason = err
                    print(f"ROW {row['id']} {index}/{len(batch)} STOP {stop_reason}", flush=True)
                    break
                print(f"ROW {row['id']} {index}/{len(batch)} SKIP {err}", flush=True)
                _save(rows)
                continue
            rank = _rank_one(row)
            if rank == "applied":
                jev_ranked += 1
            _save(rows)
            filled.append(row["id"])
            print(
                f"ROW {row['id']} {index}/{len(batch)} candidates={len(row.get('candidates') or [])} "
                f"jev={rank} status={row.get('review_status')} origin={row.get('origin')} "
                f"license={row.get('license_type')}",
                flush=True,
            )
    _save(rows)
    last_id = filled[-1] if filled else ""
    _status(rows, filled=len(filled), last_id=last_id, stop_reason=stop_reason, jev_ranked=jev_ranked)
    empty_now = [row["id"] for row in rows if _empty(row)]
    print(
        "FILL_DONE " + json.dumps({
            "source_rows": len(rows),
            "with_candidates": sum(1 for row in rows if not _empty(row)),
            "filled": len(filled),
            "last_id": last_id,
            "next_id": empty_now[0] if empty_now else "",
            "still_empty": len(empty_now),
            "stop_reason": stop_reason,
            "jev_ranked_this_process": jev_ranked,
            "weights_written": False,
            "training_started": False,
        }, ensure_ascii=False),
        flush=True,
    )
    if stop_reason == "missing_key":
        return 2
    if stop_reason and stop_reason != "time_budget":
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        print("FILL_STOP " + redact(traceback.format_exc()), flush=True)
        raise
