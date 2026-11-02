"""Fill Gemini candidates on spoken_scale.jsonl and Jev-rank each new row.

Does not rewrite kp-001–kp-100. Does not edit the frozen scale version
directory. Does not approve rows, change licence, or start training.

The key pool rolls on 503 and timeouts and waits once if every key is
cooling. If the pool is still cooling after that wait, this process stops.

Resume:
  PYTHONPATH=src .venv/bin/python data/outputs/voice_training/2026-10-23-spoken-500/fill_scale.py --limit 25 --write-split
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import time
import traceback
from pathlib import Path

from claynext.models.jev_decisions import jev_key_configured, rank_khmer_candidates
from claynext.models.khmer_spoken.providers.google_gemini_provider import GeminiTeacherProvider
from claynext.utils.paths import DATA_DIR

ROOT = Path(__file__).resolve().parents[4]
REMAINDER2 = ROOT / "data/khmer_spoken/versions/owner-approved-20261023-remainder-2/dialogue.jsonl"
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
VERSION = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
OUT_DIR = Path(__file__).resolve().parent
PROGRESS = OUT_DIR / "scale_progress.json"
SUMMARY = OUT_DIR / "scale_fill_run.json"
STATUS = OUT_DIR / "scale_status.json"
PID_PATH = OUT_DIR / "fill_scale.pid"
RESUME = (
    "PYTHONPATH=src .venv/bin/python "
    "data/outputs/voice_training/2026-10-23-spoken-500/fill_scale.py --limit 25 --write-split"
)


def redact(text: str) -> str:
    cleaned = text or ""
    cleaned = re.sub(r"AIza[\w\-]+", "[redacted]", cleaned)
    cleaned = re.sub(r"sk-[A-Za-z0-9_\-]+", "[redacted]", cleaned)
    cleaned = re.sub(r"(?i)(key|token|secret|authorization)=([^\s&\"']+)", r"\1=[redacted]", cleaned)
    cleaned = re.sub(r"(?i)bearer\s+\S+", "bearer [redacted]", cleaned)
    return cleaned[:500]


def kp_num(row_id: str) -> int:
    tail = str(row_id or "").split("-", 1)[-1]
    if not tail.isdigit():
        raise SystemExit(f"bad id {row_id}")
    return int(tail)


def enabled_gemini_keys() -> int:
    db = DATA_DIR / "claynext.db"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT COUNT(*) FROM api_keys WHERE provider = 'gemini' AND enabled = 1"
        ).fetchone()
    finally:
        con.close()
    return int(row[0] if row else 0)


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


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line if line.endswith("\n") else line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def _empty(row: dict) -> bool:
    return not any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))


def _attach(row: dict, teacher: GeminiTeacherProvider) -> tuple[bool, str]:
    frozen = (
        row.get("review_status"),
        row.get("verified_by"),
        row.get("verified_at"),
        row.get("approved_text"),
        row.get("license_type"),
        row.get("license_notes"),
        row.get("reviewer_notes"),
        row.get("stub_khmer"),
        row.get("source_text"),
    )
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
        return False, redact(f"{type(exc).__name__}: {exc}")
    if result.skipped or not result.ok:
        row["candidates"] = prior
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
        return False, "no candidates parsed"
    row["candidates"] = prior + new_cands
    if row.get("origin") == "synthetic":
        row["origin"] = "gemini_teacher"
    after = (
        row.get("review_status"),
        row.get("verified_by"),
        row.get("verified_at"),
        row.get("approved_text"),
        row.get("license_type"),
        row.get("license_notes"),
        row.get("reviewer_notes"),
        row.get("stub_khmer"),
        row.get("source_text"),
    )
    if after != frozen:
        row["candidates"] = prior
        (
            row["review_status"],
            row["verified_by"],
            row["verified_at"],
            row["approved_text"],
            row["license_type"],
            row["license_notes"],
            row["reviewer_notes"],
            row["stub_khmer"],
            row["source_text"],
        ) = frozen
        return False, "review fields changed; row reverted"
    return True, ""


def _save(rows: list[dict], head: list[str]) -> None:
    lines = list(head)
    for row in rows[len(head):]:
        lines.append(json.dumps(row, ensure_ascii=False))
    _write_lines(WORKSPACE, lines)
    disk_head = [line for line in WORKSPACE.read_text(encoding="utf-8").splitlines() if line.strip()][: len(head)]
    if disk_head != head:
        raise SystemExit("kp-001–kp-100 changed on disk; stopping")


def _rank_one(row: dict) -> str:
    if _empty(row):
        return "empty"
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
        if prior_jev is None:
            meta.pop("jev", None)
        else:
            meta["jev"] = prior_jev
        return "error"
    if not result.get("applied"):
        row["candidates"] = prior
        if prior_jev is None:
            meta.pop("jev", None)
        else:
            meta["jev"] = prior_jev
        return str(result.get("reason") or "not_applied")
    row["candidates"] = prior
    meta["jev"] = dict(example.metadata.get("jev") or result)
    if not meta["jev"].get("applied"):
        meta.pop("jev", None)
        return "not_applied"
    return "applied"


def _status(rows: list[dict], *, filled: int, last_id: str, stop_reason: str, jev_ranked: int) -> None:
    empty = [row["id"] for row in rows if kp_num(row["id"]) >= 121 and _empty(row)]
    with_cands = sum(1 for row in rows if not _empty(row))
    jev_n = sum(1 for row in rows if (row.get("metadata") or {}).get("jev", {}).get("applied"))
    payload = {
        "source_rows": len(rows),
        "with_candidates": with_cands,
        "jev_ranked_rows": jev_n,
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
        "workspace": str(WORKSPACE.relative_to(ROOT)),
        "version": str(VERSION.relative_to(ROOT)),
        "resume": RESUME,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    STATUS.write_text(text, encoding="utf-8")
    SUMMARY.write_text(text, encoding="utf-8")
    PROGRESS.write_text(json.dumps({**payload, "stopped": bool(stop_reason)}, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--max-minutes", type=float, default=80)
    parser.add_argument("--write-split", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if PID_PATH.is_file():
        try:
            old = int(PID_PATH.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            old = 0
        if old and old != os.getpid() and _alive(old):
            raise SystemExit(f"fill_scale already running pid {old}")
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
    if not WORKSPACE.is_file():
        raise SystemExit(f"missing {WORKSPACE}")
    raw = [line for line in WORKSPACE.read_text(encoding="utf-8").splitlines() if line.strip()]
    head = [line for line in REMAINDER2.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(head) != 100:
        raise SystemExit(f"remainder-2 has {len(head)} rows, expected 100")
    if raw[:100] != head:
        raise SystemExit("refusing to continue: kp-001–kp-100 no longer match remainder-2")
    rows = [json.loads(line) for line in raw]
    ids = [row["id"] for row in rows]
    if ids != [f"kp-{index:03d}" for index in range(1, len(rows) + 1)]:
        raise SystemExit("scale ids are not contiguous kp ids from kp-001")
    for row in rows[100:]:
        if row.get("review_status") != "pending_native_review":
            raise SystemExit(f"{row['id']} is not pending_native_review")
        if row.get("license_type") != "unknown":
            raise SystemExit(f"{row['id']} licence is not unknown")
        if row.get("verified_by") or row.get("approved_text"):
            raise SystemExit(f"{row['id']} looks approved")

    todo = [row for row in rows if kp_num(row["id"]) >= 121 and _empty(row)]
    limit = max(0, args.limit)
    batch = todo[:limit]
    deadline = time.monotonic() + max(1.0, args.max_minutes) * 60.0
    teacher = GeminiTeacherProvider(models=("gemini-flash-latest",))
    keys_before = enabled_gemini_keys()
    print(
        f"FILL empty={len(todo)} batch={len(batch)} gemini_available={teacher.available()} "
        f"enabled_gemini_keys={keys_before} jev={jev_key_configured()} "
        f"max_minutes={args.max_minutes}",
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
                _save(rows, head)
                continue
            _save(rows, head)
            rank = _rank_one(row)
            if rank == "applied":
                jev_ranked += 1
            _save(rows, head)
            filled.append(row["id"])
            print(
                f"ROW {row['id']} {index}/{len(batch)} candidates={len(row.get('candidates') or [])} "
                f"jev={rank} status={row.get('review_status')} origin={row.get('origin')} "
                f"license={row.get('license_type')}",
                flush=True,
            )

    _save(rows, head)
    last_id = filled[-1] if filled else ""
    if args.write_split or filled or stop_reason:
        _status(rows, filled=len(filled), last_id=last_id, stop_reason=stop_reason, jev_ranked=jev_ranked)
    empty_now = [row["id"] for row in rows if kp_num(row["id"]) >= 121 and _empty(row)]
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
            "jev_ranked_rows": sum(1 for row in rows if (row.get("metadata") or {}).get("jev", {}).get("applied")),
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
