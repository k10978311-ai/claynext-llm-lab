"""Fill Gemini candidates for synthetic rows kp-101 through kp-500.

Does not rewrite kp-001–kp-100, remainder-2, or the old held-out directory.
Does not approve rows, does not change licence, and does not start training.

Resume:
  PYTHONPATH=src .venv/bin/python data/outputs/voice_training/2026-10-23-spoken-500/fill_kp101.py --limit 25
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import traceback
from pathlib import Path

from claynext.models.jev_decisions import jev_key_configured, rank_khmer_candidates
from claynext.models.khmer_spoken.providers.google_gemini_provider import GeminiTeacherProvider
from claynext.models.khmer_spoken.schema import SCHEMA_VERSION
from claynext.utils.paths import DATA_DIR

ROOT = Path(__file__).resolve().parents[4]
REMAINDER2 = ROOT / "data/khmer_spoken/versions/owner-approved-20261023-remainder-2/dialogue.jsonl"
PARTS = [
    ROOT / "data/khmer_spoken/fixtures/synthetic_400_part1.tsv",
    ROOT / "data/khmer_spoken/fixtures/synthetic_400_part2.tsv",
    ROOT / "data/khmer_spoken/fixtures/synthetic_400_part3.tsv",
]
FIXTURE = ROOT / "data/khmer_spoken/fixtures/dialogue_400_synthetic.jsonl"
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_500.jsonl"
SPLIT = ROOT / "data/khmer_spoken/versions/train100-locked400-20261023"
OUT_DIR = Path(__file__).resolve().parent
PROGRESS = OUT_DIR / "progress.json"
SUMMARY = OUT_DIR / "fill_run.json"
HELD_OUT = ROOT / "data/khmer_spoken/versions/heldout-locked-20261023-kp081-100"
TRACKED_CANDIDATES = ROOT / "data/khmer_spoken/workspace/candidates.jsonl"
TRAIN_FIRST = 100
TRAIN_LAST = 100
LOCKED_FIRST = 101
LOCKED_LAST = 500

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the expansion to 500 rows. "
    "Original English line, not a copy of kp-001 through kp-100 and not taken "
    "from a commercial video. Licence unknown. Not gold. Not owner-approved. "
    "Pending native review."
)
REVIEWER_NOTES = (
    "Synthetic English source only. No reference Khmer. "
    "review_status pending_native_review."
)


def redact(text: str) -> str:
    cleaned = text or ""
    cleaned = re.sub(r"AIza[\w\-]+", "[redacted]", cleaned)
    cleaned = re.sub(r"(?i)(key|token|secret|authorization)=([^\s&\"']+)", r"\1=[redacted]", cleaned)
    cleaned = re.sub(r"(?i)bearer\s+\S+", "bearer [redacted]", cleaned)
    return cleaned[:500]


def file_sha(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_shas(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    if path.is_file():
        return {str(path): file_sha(path)}
    for item in sorted(path.rglob("*")):
        if item.is_file():
            out[str(item.relative_to(ROOT))] = file_sha(item)
    return out


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
        "no available gemini", "high demand", "no response",
    )):
        return "cooldown"
    return ""


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _draft_rows() -> list[dict]:
    raw: list[list[str]] = []
    for part in PARTS:
        for line in part.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            cols = line.split("\t")
            if len(cols) != 8:
                raise SystemExit(f"{part} has a row with {len(cols)} columns")
            raw.append(cols)
    if len(raw) != 400:
        raise SystemExit(f"expected 400 synthetic lines, got {len(raw)}")
    texts = [cols[7].strip() for cols in raw]
    if len(set(texts)) != 400:
        raise SystemExit("synthetic source lines are not unique")
    rows = []
    for index, cols in enumerate(raw, start=LOCKED_FIRST):
        category, relationship, speaker, listener, emotion, register, setting, text = cols
        rows.append({
            "id": f"kp-{index:03d}",
            "source_text": text.strip(),
            "source_lang": "en",
            "target_lang": "km",
            "stub_khmer": "",
            "candidates": [],
            "approved_text": "",
            "speaker_id": speaker.strip(),
            "listener_id": listener.strip(),
            "relationship": relationship.strip(),
            "emotion": emotion.strip() or "neutral",
            "register": register.strip() or "neutral",
            "category": category.strip() or "everyday",
            "origin": "synthetic",
            "license_type": "unknown",
            "license_notes": LICENSE_NOTES,
            "review_status": "pending_native_review",
            "verified_by": "",
            "verified_at": "",
            "reviewer_notes": REVIEWER_NOTES,
            "metadata": {
                "provenance": "synthetic_draft",
                "synthetic_draft": True,
                "source_file": "data/khmer_spoken/fixtures/dialogue_400_synthetic.jsonl",
                "licence": None,
                "not_for_gold": True,
                "not_for_weight_training": True,
                "locked_from_training": True,
                "setting": setting.strip(),
                "expansion": "kp-101-kp-500",
                "created_on": "2026-10-23",
                "note": "Synthetic draft. No external licence was invented.",
            },
            "schema_version": SCHEMA_VERSION,
        })
    return rows


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line if line.endswith("\n") else line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def ensure_sources() -> list[dict]:
    drafts = _draft_rows()
    if not FIXTURE.is_file():
        _write_lines(FIXTURE, [json.dumps(row, ensure_ascii=False) for row in drafts])
    finished_lines = [line for line in REMAINDER2.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(finished_lines) != 100:
        raise SystemExit(f"remainder-2 has {len(finished_lines)} rows, expected 100")
    finished = [json.loads(line) for line in finished_lines]
    if [row["id"] for row in finished] != [f"kp-{i:03d}" for i in range(1, 101)]:
        raise SystemExit("remainder-2 ids are not kp-001 through kp-100")
    if not WORKSPACE.is_file():
        draft_lines = [json.dumps(row, ensure_ascii=False) for row in drafts]
        _write_lines(WORKSPACE, finished_lines + draft_lines)
    rows = _load_jsonl(WORKSPACE)
    if len(rows) != 500:
        raise SystemExit(f"spoken_500 has {len(rows)} rows, expected 500")
    if [row["id"] for row in rows] != [f"kp-{i:03d}" for i in range(1, 501)]:
        raise SystemExit("spoken_500 ids are not kp-001 through kp-500")
    for old, new in zip(finished, rows[:100]):
        if old != new:
            raise SystemExit(f"refusing to continue: {new['id']} no longer matches remainder-2")
    for row in rows[100:]:
        if row.get("review_status") != "pending_native_review":
            raise SystemExit(f"{row['id']} is not pending_native_review")
        if row.get("license_type") != "unknown":
            raise SystemExit(f"{row['id']} licence is not unknown")
        if row.get("verified_by") or row.get("approved_text"):
            raise SystemExit(f"{row['id']} looks approved")
    return rows


def _protected_snapshot() -> dict[str, str]:
    found = {}
    found.update(tree_shas(REMAINDER2.parent))
    found.update(tree_shas(HELD_OUT))
    found[str(TRACKED_CANDIDATES.relative_to(ROOT))] = file_sha(TRACKED_CANDIDATES)
    return found


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
    row["candidates"] = prior
    if not new_cands:
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
        ) = frozen
        return False, "review fields changed; row reverted"
    return True, ""


def _save(rows: list[dict], finished_lines: list[str]) -> None:
    lines = []
    for index, row in enumerate(rows):
        if index < 100:
            lines.append(finished_lines[index])
            continue
        lines.append(json.dumps(row, ensure_ascii=False))
    _write_lines(WORKSPACE, lines)


def _rank_new(rows: list[dict], ids: list[str]) -> dict:
    if not ids:
        return {"ran": False, "reason": "no_new_candidates", "ranked": 0, "unchanged": 0, "ids": []}
    if not jev_key_configured():
        return {"ran": False, "reason": "no_key", "ranked": 0, "unchanged": 0, "ids": []}
    wanted = set(ids)
    ranked_ids: list[str] = []
    reasons: dict[str, str] = {}
    for row in rows:
        if row["id"] not in wanted:
            continue
        if _empty(row):
            continue
        if (row.get("metadata") or {}).get("jev", {}).get("applied"):
            continue
        prior = json.loads(json.dumps(row.get("candidates") or []))
        meta = row.setdefault("metadata", {})
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
            reasons[row["id"]] = "error"
            continue
        if not result.get("applied"):
            row["candidates"] = prior
            if prior_jev is None:
                meta.pop("jev", None)
            else:
                meta["jev"] = prior_jev
            reasons[row["id"]] = str(result.get("reason") or "not_applied")
            continue
        row["candidates"] = prior
        meta["jev"] = dict(example.metadata.get("jev") or result)
        if not meta["jev"].get("applied"):
            meta.pop("jev", None)
            reasons[row["id"]] = "not_applied"
            continue
        ranked_ids.append(row["id"])
        reasons[row["id"]] = "applied"
    return {
        "ran": True,
        "reason": "",
        "ranked": len(ranked_ids),
        "unchanged": len(reasons) - len(ranked_ids),
        "ids": ranked_ids,
        "reasons": reasons,
    }


def write_split(rows: list[dict], *, filled: int, last_id: str, stop_reason: str) -> None:
    SPLIT.mkdir(parents=True, exist_ok=True)
    train_src = REMAINDER2.read_bytes()
    train_path = SPLIT / "train.jsonl"
    if train_path.is_file() and train_path.read_bytes() != train_src:
        raise SystemExit("refusing to overwrite train.jsonl; it no longer matches remainder-2")
    train_path.write_bytes(train_src)
    locked = rows[100:]
    _write_lines(SPLIT / "locked.jsonl", [json.dumps(row, ensure_ascii=False) for row in locked])
    with_cands = sum(1 for row in rows if not _empty(row))
    locked_with = sum(1 for row in locked if not _empty(row))
    manifest = {
        "version": "train100-locked400-20261023",
        "created_on": "2026-10-23",
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "promotion": "not_promoted",
        "hosted_fine_tune": "not_started",
        "licence": "unknown",
        "invented_external_licence": False,
        "owner_request": "data up to 500 rows, then 100 for training",
        "supersedes": "heldout-locked-20261023-kp081-100",
        "supersedes_note": (
            "The previous plan locked kp-081–kp-100 as test and trained on kp-001–kp-080. "
            "That directory was not overwritten. This plan replaces it: the 100 training rows "
            "are kp-001–kp-100, and kp-101–kp-500 stay locked."
        ),
        "split": {
            "rule": "stable id range",
            "train_count": 100,
            "locked_count": 400,
            "train_ids": "kp-001 through kp-100 inclusive",
            "locked_ids": "kp-101 through kp-500 inclusive",
            "train_id_first": "kp-001",
            "train_id_last": "kp-100",
            "locked_id_first": "kp-101",
            "locked_id_last": "kp-500",
            "tune_on_locked": False,
            "train_on_locked": False,
            "locked_use": "benchmark pool only; never training and never hyperparameter tuning",
        },
        "train_source": str(REMAINDER2),
        "locked_review_status": "pending_native_review",
        "locked_origin_note": "synthetic drafts until a teacher candidate is attached; still not gold",
        "workspace": str(WORKSPACE.relative_to(ROOT)),
        "rows_total": len(rows),
        "rows_with_candidates": with_cands,
        "locked_with_candidates": locked_with,
        "filled_this_process": filled,
        "last_id": last_id,
        "stop_reason": stop_reason,
        "resume": (
            "PYTHONPATH=src .venv/bin/python "
            "data/outputs/voice_training/2026-10-23-spoken-500/fill_kp101.py --limit 25"
        ),
    }
    (SPLIT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--write-split", action="store_true")
    parser.add_argument("--sources-only", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    protected_before = _protected_snapshot()
    rows = ensure_sources()
    finished_lines = [line for line in REMAINDER2.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.sources_only:
        if args.write_split:
            write_split(rows, filled=0, last_id="", stop_reason="sources_only")
        print(f"SOURCES rows={len(rows)} workspace={WORKSPACE}", flush=True)
        return 0

    todo = [row for row in rows if row["id"] >= "kp-101" and _empty(row)]
    # ids are zero-padded, so string compare works for kp-001..kp-500
    limit = max(0, args.limit)
    batch = todo[:limit]
    teacher = GeminiTeacherProvider(models=("gemini-flash-latest",))
    keys_before = enabled_gemini_keys()
    print(
        f"FILL empty={len(todo)} batch={len(batch)} gemini_available={teacher.available()} "
        f"enabled_gemini_keys={keys_before} jev={jev_key_configured()}",
        flush=True,
    )
    filled: list[str] = []
    stop_reason = ""
    if not teacher.available():
        stop_reason = "missing_key"
    else:
        for index, row in enumerate(batch, start=1):
            ok, err = _attach(row, teacher)
            if not ok:
                kind = _stop_class(err)
                if kind in {"auth", "cooldown"}:
                    stop_reason = err
                    print(f"ROW {row['id']} {index}/{len(batch)} STOP {stop_reason}", flush=True)
                    break
                print(f"ROW {row['id']} {index}/{len(batch)} SKIP {err}", flush=True)
                _save(rows, finished_lines)
                continue
            filled.append(row["id"])
            _save(rows, finished_lines)
            # Confirm the finished hundred were not rewritten on disk.
            disk_head = [line for line in WORKSPACE.read_text(encoding="utf-8").splitlines() if line.strip()][:100]
            if disk_head != finished_lines:
                raise SystemExit("kp-001–kp-100 changed on disk; stopping")
            PROGRESS.write_text(json.dumps({
                "filled_this_process": len(filled),
                "last_id": row["id"],
                "candidates": len(row.get("candidates") or []),
                "stopped": False,
            }, ensure_ascii=False) + "\n", encoding="utf-8")
            print(
                f"ROW {row['id']} {index}/{len(batch)} candidates={len(row.get('candidates') or [])} "
                f"status={row.get('review_status')} origin={row.get('origin')} license={row.get('license_type')}",
                flush=True,
            )

    _save(rows, finished_lines)
    jev = _rank_new(rows, filled) if filled else {
        "ran": False, "reason": "no_new_candidates", "ranked": 0, "unchanged": 0, "ids": [],
    }
    if jev.get("ranked"):
        _save(rows, finished_lines)
    print(
        f"JEV ran={jev['ran']} ranked={jev['ranked']} unchanged={jev['unchanged']} "
        f"reason={jev['reason'] or 'ok'}",
        flush=True,
    )
    last_id = filled[-1] if filled else ""
    if args.write_split or filled or stop_reason:
        write_split(rows, filled=len(filled), last_id=last_id, stop_reason=stop_reason)
    protected_after = _protected_snapshot()
    empty_now = [row["id"] for row in rows if row["id"] >= "kp-101" and _empty(row)]
    summary = {
        "source_rows": len(rows),
        "with_candidates": sum(1 for row in rows if not _empty(row)),
        "locked_with_candidates": sum(1 for row in rows[100:] if not _empty(row)),
        "empty_at_start": len(todo),
        "batch": len(batch),
        "filled": len(filled),
        "filled_ids": filled,
        "still_empty": len(empty_now),
        "next_id": empty_now[0] if empty_now else "",
        "last_id": last_id,
        "stop_reason": stop_reason,
        "jev_ran": jev["ran"],
        "jev_ranked": jev["ranked"],
        "jev_unchanged": jev["unchanged"],
        "jev_reason": jev["reason"],
        "weights_written": False,
        "training_started": False,
        "promotion": "not_promoted",
        "protected_unchanged": protected_before == protected_after,
        "enabled_gemini_keys_before": keys_before,
        "enabled_gemini_keys_after": enabled_gemini_keys(),
        "workspace": str(WORKSPACE.relative_to(ROOT)),
        "split": str(SPLIT.relative_to(ROOT)),
        "train_ids": "kp-001 through kp-100",
        "locked_ids": "kp-101 through kp-500",
        "resume": (
            "PYTHONPATH=src .venv/bin/python "
            "data/outputs/voice_training/2026-10-23-spoken-500/fill_kp101.py --limit 25 --write-split"
        ),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROGRESS.write_text(json.dumps({**summary, "stopped": bool(stop_reason)}, ensure_ascii=False) + "\n", encoding="utf-8")
    print("FILL_DONE " + json.dumps({
        "source_rows": summary["source_rows"],
        "with_candidates": summary["with_candidates"],
        "filled": summary["filled"],
        "last_id": summary["last_id"],
        "next_id": summary["next_id"],
        "still_empty": summary["still_empty"],
        "stop_reason": summary["stop_reason"],
        "jev_ranked": summary["jev_ranked"],
        "protected_unchanged": summary["protected_unchanged"],
        "weights_written": False,
        "training_started": False,
    }, ensure_ascii=False), flush=True)
    if not summary["protected_unchanged"]:
        return 3
    if stop_reason == "missing_key":
        return 2
    return 0 if not stop_reason else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        print("FILL_STOP " + redact(traceback.format_exc()), flush=True)
        raise
