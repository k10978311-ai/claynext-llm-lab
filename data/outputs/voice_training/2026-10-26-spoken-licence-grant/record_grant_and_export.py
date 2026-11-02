"""Record a project-owner licence grant and refresh the translation SFT export.

Reads spoken_scale.jsonl. Does not edit it, the open 720-line SFT file, the
scale lock, or older version directories. Calls trainer.start and records the
refusal. Does not install a trainer and does not write weights.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.khmer_spoken.schema import DialogueExample
from claynext.models.training.trainer import start, training_implementation_available

ROOT = Path(__file__).resolve().parents[4]
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
OPEN_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl"
GRANT_DIR = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261026"
SFT_DIR = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-b"
CONFIG_DIR = ROOT / "src/claynext/models/training/configs"
FILL_LOG = ROOT / "data/outputs/voice_training/2026-10-23-spoken-500/fill_scale.log"
FILL_PID = 58618
OWNER_QUOTE = "if licence is still unknown i approve you do sometihnk and continue trained."
GRANT_STATEMENT = (
    "The project owner approved training use of the listed train-pool spoken Khmer rows "
    "while license_type remains unknown. This grant is not CC-BY and not any other "
    "external licence. Holdout rows kp-1001–kp-2000 are not included and were not changed."
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def kp_num(row_id: str) -> int:
    tail = str(row_id).split("-", 1)[-1]
    if not tail.isdigit():
        raise SystemExit(f"bad id {row_id}")
    return int(tail)


def has_khmer(text: str) -> bool:
    return any("\u1780" <= ch <= "\u17ff" for ch in text)


def jev_text(row: dict) -> str:
    jev = (row.get("metadata") or {}).get("jev") or {}
    text = str(jev.get("preferred_text") or "").strip()
    if not jev.get("applied") or not text:
        return ""
    if any(str((cand or {}).get("text") or "") == text for cand in (row.get("candidates") or [])):
        return text
    return ""


def has_candidate(row: dict) -> bool:
    return any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))


def load_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pid_alive(pid: int) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["ps", "-p", str(pid), "-o", "pid=,ppid=,etime=,command="],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return False, f"ps failed: {exc}"
    line = proc.stdout.strip()
    return bool(line), line


def read_snapshot() -> tuple[bytes, list[dict]]:
    expected = [f"kp-{index:03d}" for index in range(1, 2001)]
    last_error = "no read"
    for _ in range(12):
        raw = WORKSPACE.read_bytes()
        try:
            text = raw.decode("utf-8")
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(0.05)
            continue
        ids = [row.get("id") for row in rows]
        if ids != expected:
            last_error = f"ids {ids[:1]}..{ids[-1:]} count={len(rows)}"
            time.sleep(0.05)
            continue
        return raw, rows
    raise SystemExit(f"could not read a complete spoken_scale snapshot: {last_error}")


def log_tail() -> str:
    if not FILL_LOG.is_file():
        return ""
    lines = FILL_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        if line.startswith("ROW ") or line.startswith("FILL"):
            return line
    return lines[-1] if lines else ""


def main() -> None:
    if GRANT_DIR.exists() or SFT_DIR.exists():
        raise SystemExit("refusing to overwrite the licence grant or the new SFT directory")
    open_sft_sha = sha256_file(OPEN_SFT)
    open_sft_lines = sum(1 for line in OPEN_SFT.read_text(encoding="utf-8").splitlines() if line.strip())
    if open_sft_lines != 720:
        raise SystemExit(f"open sft.jsonl has {open_sft_lines} lines, expected 720")
    lock_hashes = {
        "manifest.json": sha256_file(LOCK / "manifest.json"),
        "train_ids.txt": sha256_file(LOCK / "train_ids.txt"),
        "locked_ids.txt": sha256_file(LOCK / "locked_ids.txt"),
    }
    train_ids = load_ids(LOCK / "train_ids.txt")
    locked_ids = load_ids(LOCK / "locked_ids.txt")
    expected_train = [f"kp-{index:03d}" for index in range(1, 1001)]
    expected_locked = [f"kp-{index:03d}" for index in range(1001, 2001)]
    if train_ids != expected_train or locked_ids != expected_locked:
        raise SystemExit("scale lock on disk is not train kp-001–kp-1000 and holdout kp-1001–kp-2000")
    locked_set = set(locked_ids)
    alive, ps_line = pid_alive(FILL_PID)
    raw, rows = read_snapshot()
    snapshot_sha = sha256_bytes(raw)
    by_id = {row["id"]: row for row in rows}
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    sft_rows: list[dict] = []
    grants: list[dict] = []
    excluded_non_unknown = []
    gold_differs = 0
    live_gold = 0
    live_pending = 0
    for row_id in train_ids:
        row = by_id[row_id]
        ranked = jev_text(row)
        if not ranked:
            continue
        example = DialogueExample.from_dict(row)
        target = example.training_khmer().strip()
        source = example.source_text.strip()
        if target != ranked:
            raise SystemExit(f"{row_id} training_khmer did not keep the Jev line")
        if not source or not target or source == target:
            raise SystemExit(f"{row_id} source or Khmer is empty or identical")
        if not has_khmer(target) or has_khmer(source):
            raise SystemExit(f"{row_id} source/Khmer script check failed")
        if row_id in locked_set or kp_num(row_id) > 1000:
            raise SystemExit(f"{row_id} is holdout")
        if example.license_type != "unknown":
            excluded_non_unknown.append(row_id)
            continue
        approved = str(row.get("approved_text") or "").strip()
        if example.review_status == "gold":
            live_gold += 1
            if approved and approved != ranked:
                gold_differs += 1
        elif example.review_status == "pending_native_review":
            live_pending += 1
        else:
            raise SystemExit(f"{row_id} unexpected review_status {example.review_status}")
        sft_rows.append({
            "id": row_id,
            "source": source,
            "khmer": target,
            "licence": "unknown",
            "owner_training_approved": True,
            "split": "train",
        })
        grants.append({
            "id": row_id,
            "license_type": "unknown",
            "licence": "unknown",
            "owner_training_approved": True,
            "grant": "project-owner approval to train on this row despite unknown licence",
            "external_licence": None,
            "invented_external_licence": False,
            "split": "train",
            "holdout": False,
            "promotion": "not_promoted",
            "marked_gold": False,
            "live_file_edited": False,
            "quote": OWNER_QUOTE,
            "by": "project-owner",
        })

    exported_ids = [row["id"] for row in sft_rows]
    if any(row_id in locked_set for row_id in exported_ids):
        raise SystemExit("export contains a holdout id")
    holdout_with_candidates = [
        row["id"] for row in rows if row["id"] in locked_set and has_candidate(row)
    ]
    empty_train = [row_id for row_id in train_ids if not jev_text(by_id[row_id])]
    cand_ids = [row["id"] for row in rows if has_candidate(row) and kp_num(row["id"]) <= 1000]
    last_cand = cand_ids[-1] if cand_ids else ""
    gaps = []
    if exported_ids:
        numbers = [kp_num(row_id) for row_id in exported_ids]
        if numbers[0] != 1:
            gaps.append(f"does not start at kp-001 ({exported_ids[0]})")
        for prev, nxt in zip(numbers, numbers[1:]):
            if nxt != prev + 1:
                gaps.append(f"kp-{prev:03d} -> kp-{nxt:03d}")

    included_first = exported_ids[0] if exported_ids else ""
    included_last = exported_ids[-1] if exported_ids else ""
    range_text = f"{included_first}–{included_last}" if exported_ids else ""

    configs = [
        "sft_lora_3b.yaml",
        "qlora_7b_8b.yaml",
        "qlora_14b.yaml",
        "dpo_3b.yaml",
    ]
    trainer_results = []
    for name in configs:
        result = start(CONFIG_DIR / name, approval=True)
        if result.get("started") or result.get("weights"):
            raise SystemExit(f"{name} reported a start or weights; aborting without a follow-up launch")
        trainer_results.append({
            "config": f"src/claynext/models/training/configs/{name}",
            "approval_flag": True,
            "status": result.get("status"),
            "started": result.get("started"),
            "reason": result.get("reason"),
            "weights": result.get("weights"),
            "machine_blocked": (result.get("validation") or {}).get("machine_blocked"),
            "size_class": (result.get("validation") or {}).get("size_class"),
        })
    trainer_installed = training_implementation_available()
    primary = trainer_results[0]

    GRANT_DIR.mkdir(parents=True)
    SFT_DIR.mkdir(parents=True)
    sft_path = SFT_DIR / "sft-train-approved.jsonl"
    sft_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sft_rows),
        encoding="utf-8",
    )
    (SFT_DIR / "exported_ids.txt").write_text(
        "".join(f"{row_id}\n" for row_id in exported_ids),
        encoding="utf-8",
    )
    (GRANT_DIR / "train_ids.txt").write_text(
        "".join(f"{row_id}\n" for row_id in exported_ids),
        encoding="utf-8",
    )
    (GRANT_DIR / "grants.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in grants),
        encoding="utf-8",
    )

    grant_manifest = {
        "version": "owner-licence-grant-20261026",
        "schema": "spoken-owner-licence-grant-1",
        "created_at": created,
        "statement": GRANT_STATEMENT,
        "owner_quote": OWNER_QUOTE,
        "owner_quote_scope": (
            "Project-owner approval to train on the listed train-pool rows while licence "
            "stays unknown. Not an external licence. Not approval to change holdout rows, "
            "invent CC-BY, mark native gold, promote, call Vertex, or launch a 3B, 7B, 8B, "
            "or 14B fine-tune on this 16 GB M4."
        ),
        "grant": "project-owner approval to train on these rows despite unknown licence",
        "by": "project-owner",
        "licence": "unknown",
        "license_type": "unknown",
        "external_licence": None,
        "invented_external_licence": False,
        "owner_training_approved": True,
        "applied_to_live_jsonl": False,
        "live_jsonl_edited": False,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "holdout_changed": False,
        "holdout_included": False,
        "promotion": "not_promoted",
        "newly_marked_gold": 0,
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "id_first": included_first,
        "id_last": included_last,
        "id_range": range_text,
        "included_count": len(exported_ids),
        "included_ids_file": "data/khmer_spoken/versions/owner-licence-grant-20261026/train_ids.txt",
        "train_pool": "kp-001–kp-1000",
        "holdout": "kp-1001–kp-2000",
        "train_pool_without_jev_excluded": len(empty_train),
        "excluded_non_unknown_licence": excluded_non_unknown,
        "gaps": gaps,
        "snapshot_sha256": snapshot_sha,
        "snapshot_rows": len(rows),
        "snapshot_note": (
            "Read while fill pid 58618 may still be replacing spoken_scale.jsonl. "
            "This grant lists only the train ids that had a Jev Khmer line in that read. "
            "Rows saved after the read are not in this grant."
        ),
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
    }
    (GRANT_DIR / "manifest.json").write_text(
        json.dumps(grant_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    sft_manifest = {
        "version": "translate-sft-spoken-20261026-b",
        "schema": "spoken-translate-sft-approved-1",
        "created_at": created,
        "dry_run": True,
        "started": False,
        "training_started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "trainer_installed": trainer_installed,
        "promotion": "not_promoted",
        "hosted_fine_tune": "not_started",
        "vertex_fine_tune": "not_called",
        "licence": "unknown",
        "owner_training_approved": True,
        "invented_external_licence": False,
        "native_gold_benchmark": False,
        "not_the_1000_to_2000_native_gold_benchmark": True,
        "newly_marked_gold": 0,
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "teacher": "gemini",
        "ranker": "jev",
        "gemini_and_jev_are_not_a_weight_update": True,
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "owner_quote": OWNER_QUOTE,
        "licence_grant": "data/khmer_spoken/versions/owner-licence-grant-20261026",
        "licence_grant_statement": GRANT_STATEMENT,
        "target_rule": (
            "DialogueExample.training_khmer(). The khmer field is the Jev line when it "
            "matches a candidate. The stub is not used. Holdout ids are excluded. "
            "The open 720-line sft.jsonl was not rewritten."
        ),
        "prior_open_sft": "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl",
        "prior_open_sft_left_unmodified": True,
        "prior_open_sft_lines_before": open_sft_lines,
        "prior_open_sft_sha256_before": open_sft_sha,
        "path": "data/khmer_spoken/versions/translate-sft-spoken-20261026-b/sft-train-approved.jsonl",
        "row_count": len(exported_ids),
        "id_first": included_first,
        "id_last": included_last,
        "id_range": range_text,
        "split": "train",
        "fields": ["id", "source", "khmer", "licence", "owner_training_approved", "split"],
        "from_jev_count": len(exported_ids),
        "stub_used_count": 0,
        "holdout_excluded": True,
        "holdout_ids_in_export": 0,
        "holdout_with_candidates_at_snapshot": len(holdout_with_candidates),
        "holdout_with_candidates_ids": holdout_with_candidates[:20],
        "live_review_status_among_exported": {
            "gold": live_gold,
            "pending_native_review": live_pending,
        },
        "gold_approved_text_differs_from_jev": gold_differs,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "live_jsonl_edited": False,
        "snapshot_sha256": snapshot_sha,
        "snapshot_rows": len(rows),
        "last_train_id_with_candidates": last_cand,
        "next_train_id_without_jev": empty_train[0] if empty_train else "",
        "train_pool_without_jev": len(empty_train),
        "gaps": gaps,
        "sft_sha256": sha256_file(sft_path),
        "lock": {
            "version": "scale-lock1000-20261023",
            "train_id_first": "kp-001",
            "train_id_last": "kp-1000",
            "locked_id_first": "kp-1001",
            "locked_id_last": "kp-2000",
            "train_count": len(train_ids),
            "locked_count": len(locked_ids),
            "hashes": lock_hashes,
            "prior_directories_deleted": False,
        },
        "trainer_start_called": True,
        "trainer_start_approval_flag": True,
        "trainer_start_note": (
            "approval=True was passed because the project owner approved continuing "
            "training. trainer.start still refused. started stays false. No weights were written."
        ),
        "trainer_primary_config": primary["config"],
        "trainer_primary_status": primary["status"],
        "trainer_primary_reason": primary["reason"],
        "trainer_results": trainer_results,
        "fill_at_snapshot": {
            "pid": FILL_PID,
            "alive": alive,
            "ps": ps_line,
            "log_tail": log_tail(),
            "second_fill_started": False,
            "reason": "pid 58618 was alive, so spoken_scale.jsonl was not edited and no second fill was started",
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
    }
    if sha256_file(OPEN_SFT) != open_sft_sha:
        raise SystemExit("the open 720-line sft.jsonl changed")
    if sha256_file(LOCK / "locked_ids.txt") != lock_hashes["locked_ids.txt"]:
        raise SystemExit("scale lock changed")
    sft_manifest["prior_open_sft_sha256_after"] = sha256_file(OPEN_SFT)
    (SFT_DIR / "manifest.json").write_text(
        json.dumps(sft_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    alive_after, ps_after = pid_alive(FILL_PID)
    print(json.dumps({
        "grant_dir": "data/khmer_spoken/versions/owner-licence-grant-20261026",
        "id_range": range_text,
        "included_count": len(exported_ids),
        "gaps": gaps,
        "sft_path": sft_manifest["path"],
        "sft_rows": len(exported_ids),
        "open_sft_lines": open_sft_lines,
        "open_sft_unchanged": True,
        "holdout_in_export": 0,
        "holdout_with_candidates": len(holdout_with_candidates),
        "train_pool_without_jev": len(empty_train),
        "next_without_jev": empty_train[0] if empty_train else "",
        "last_train_with_candidates": last_cand,
        "live_gold": live_gold,
        "live_pending": live_pending,
        "gold_differs_from_jev": gold_differs,
        "trainer_status": primary["status"],
        "trainer_reason": primary["reason"],
        "trainer_started": primary["started"],
        "weights_written": False,
        "trainer_installed": trainer_installed,
        "fill_pid": FILL_PID,
        "fill_alive_before": alive,
        "fill_alive_after": alive_after,
        "fill_ps_after": ps_after,
        "second_fill_started": False,
        "snapshot_sha256": snapshot_sha,
        "log_tail": sft_manifest["fill_at_snapshot"]["log_tail"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
