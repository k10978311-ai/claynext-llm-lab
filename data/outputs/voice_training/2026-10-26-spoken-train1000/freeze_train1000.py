"""Freeze the finished 1,000-row spoken train cut.

Reads spoken_scale.jsonl. Writes a new approval sidecar, a licence-use grant,
and a translation SFT export. Does not edit the live file, the open 720-line
SFT file, the 758-row SFT file, or the scale lock. Does not fill rows and does
not call trainer.start.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.khmer_spoken.schema import DialogueExample

ROOT = Path(__file__).resolve().parents[4]
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
OPEN_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl"
PRIOR_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-b/sft-train-approved.jsonl"
PRIOR_GRANT = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261026"
PRIOR_SIDECARS = (
    ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261023",
    ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026",
    ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026-next",
)
SIDECAR_DIR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026-kp1000"
GRANT_DIR = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000"
SFT_DIR = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-c"
OWNER_QUOTE = "if licence is still unknown i approve you do sometihnk and continue trained."
GRANT_STATEMENT = (
    "The project owner approved training use of the listed train-pool spoken Khmer rows "
    "while license_type remains unknown. This grant is not CC-BY and not any other "
    "external licence. Holdout rows kp-1001–kp-2000 are not included and were not changed."
)
KEY_MARKERS = ("AIza", "sk-", "hf_", "ghp_", "xoxb-", "api_key", "BEGIN PRIVATE")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def kp_num(row_id: str) -> int:
    tail = str(row_id).split("-", 1)[-1]
    if not tail.isdigit():
        raise SystemExit(f"bad id {row_id}")
    return int(tail)


def has_khmer(text: str) -> bool:
    return any("\u1780" <= ch <= "\u17ff" for ch in text)


def load_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def has_candidate(row: dict) -> bool:
    return any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))


def jev_text(row: dict) -> str:
    jev = (row.get("metadata") or {}).get("jev") or {}
    text = str(jev.get("preferred_text") or "").strip()
    if not jev.get("applied") or not text:
        return ""
    if any(str((cand or {}).get("text") or "") == text for cand in (row.get("candidates") or [])):
        return text
    return ""


def jev_index(row: dict) -> object:
    jev = (row.get("metadata") or {}).get("jev") or {}
    return jev.get("preferred_index")


def line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def read_stable_snapshot() -> tuple[bytes, list[dict]]:
    first = WORKSPACE.read_bytes()
    second = WORKSPACE.read_bytes()
    if first != second:
        raise SystemExit("spoken_scale.jsonl changed between two reads; nothing written")
    rows = [json.loads(line) for line in first.decode("utf-8").splitlines() if line.strip()]
    expected = [f"kp-{index:03d}" for index in range(1, 2001)]
    if [row.get("id") for row in rows] != expected:
        raise SystemExit("spoken_scale ids are not kp-001–kp-2000; nothing written")
    return first, rows


def fill_alive() -> bool:
    proc = subprocess.run(
        ["pgrep", "-fl", "fill_scale.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    return bool(proc.stdout.strip())


def remove_new_dirs() -> None:
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            shutil.rmtree(path)


def main() -> None:
    if fill_alive():
        raise SystemExit("fill_scale.py is running; nothing written")
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            raise SystemExit(f"refusing to overwrite {path}")
    if not OPEN_SFT.is_file() or not PRIOR_SFT.is_file():
        raise SystemExit("a prior SFT file is missing; nothing written")

    open_sft_sha = sha256_file(OPEN_SFT)
    prior_sft_sha = sha256_file(PRIOR_SFT)
    open_sft_lines = line_count(OPEN_SFT)
    prior_sft_lines = line_count(PRIOR_SFT)
    if open_sft_lines != 720 or prior_sft_lines != 758:
        raise SystemExit(
            f"prior SFT line counts are {open_sft_lines} and {prior_sft_lines}; nothing written"
        )

    train_ids = load_ids(LOCK / "train_ids.txt")
    locked_ids = load_ids(LOCK / "locked_ids.txt")
    expected_train = [f"kp-{index:03d}" for index in range(1, 1001)]
    expected_locked = [f"kp-{index:03d}" for index in range(1001, 2001)]
    if train_ids != expected_train or locked_ids != expected_locked:
        raise SystemExit("scale lock is not train kp-001–kp-1000 and holdout kp-1001–kp-2000")
    locked_bytes = (LOCK / "locked_ids.txt").read_bytes()
    locked_sha = sha256_bytes(locked_bytes)

    prior_approved: set[str] = set()
    prior_counts: dict[str, int] = {}
    for prior in PRIOR_SIDECARS:
        found = load_ids(prior / "approval_ids.txt")
        overlap = prior_approved & set(found)
        if overlap:
            raise SystemExit("prior approval sidecars overlap; nothing written")
        prior_approved.update(found)
        prior_counts[prior.name] = len(found)
    if sorted(prior_approved, key=kp_num) != [f"kp-{index:03d}" for index in range(101, 734)]:
        raise SystemExit("prior sidecars are not exactly kp-101–kp-733; nothing written")

    raw, rows = read_stable_snapshot()
    snapshot_sha = sha256_bytes(raw)
    by_id = {row["id"]: row for row in rows}
    train_rows = [by_id[row_id] for row_id in train_ids]
    hold_rows = [by_id[row_id] for row_id in locked_ids]
    train_filled = [row["id"] for row in train_rows if has_candidate(row) and jev_text(row)]
    train_empty = [row["id"] for row in train_rows if row["id"] not in set(train_filled)]
    holdout_filled = [row["id"] for row in hold_rows if has_candidate(row) or jev_text(row)]
    if len(train_filled) != 1000 or train_empty or holdout_filled:
        raise SystemExit(
            "counts are not train_filled 1000, train_empty 0, holdout_filled 0: "
            f"train_filled={len(train_filled)} train_empty={len(train_empty)} "
            f"holdout_filled={len(holdout_filled)}; nothing written"
        )
    if train_filled != expected_train:
        raise SystemExit("train fill is not contiguous kp-001–kp-1000; nothing written")

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    approvals: list[dict] = []
    for row_id in expected_train:
        row = by_id[row_id]
        number = kp_num(row_id)
        if row_id in prior_approved or number <= 100:
            continue
        if str(row.get("review_status") or "") != "pending_native_review":
            raise SystemExit(f"{row_id} is not pending_native_review; nothing written")
        if str(row.get("license_type") or "") != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown; nothing written")
        if row.get("verified_by") or str(row.get("approved_text") or "").strip():
            raise SystemExit(f"{row_id} already has a live approval; nothing written")
        ranked = jev_text(row)
        example = DialogueExample.from_dict(row)
        if example.training_khmer().strip() != ranked or not has_khmer(ranked):
            raise SystemExit(f"{row_id} Jev line check failed; nothing written")
        source = example.source_text.strip()
        if not source or source == ranked or has_khmer(source):
            raise SystemExit(f"{row_id} source check failed; nothing written")
        approvals.append({
            "id": row_id,
            "decision": "approve",
            "from_status": "pending_native_review",
            "review_status": "approved",
            "verified_by": "project-owner",
            "verified_at": created,
            "license_type": "unknown",
            "invented_external_licence": False,
            "origin": row.get("origin") or "",
            "approved_text": ranked,
            "candidate_count": sum(
                1 for cand in (row.get("candidates") or []) if str((cand or {}).get("text") or "").strip()
            ),
            "candidate_provider": "gemini_teacher",
            "jev_applied": True,
            "jev_preferred_index": jev_index(row),
            "prior_reviewer_notes": str(row.get("reviewer_notes") or ""),
            "prior_review_status": "pending_native_review",
            "history_kept": True,
            "not_gold": True,
            "training_export_approved": True,
            "not_for_weight_training": False,
            "weight_training_started": False,
            "promotion": "not_promoted",
            "purpose": "training-export",
            "quote": OWNER_QUOTE,
            "by": "project-owner",
            "live_file_edited": False,
            "split": "train",
        })

    approval_ids = [row["id"] for row in approvals]
    if approval_ids != [f"kp-{index:03d}" for index in range(734, 1001)]:
        raise SystemExit(
            f"new sidecar range is {approval_ids[:1]}..{approval_ids[-1:]} "
            f"count {len(approval_ids)}; nothing written"
        )

    sft_rows: list[dict] = []
    grants: list[dict] = []
    live_gold = 0
    live_pending = 0
    gold_differs = 0
    for row_id in expected_train:
        row = by_id[row_id]
        ranked = jev_text(row)
        example = DialogueExample.from_dict(row)
        target = example.training_khmer().strip()
        source = example.source_text.strip()
        if target != ranked or example.license_type != "unknown":
            raise SystemExit(f"{row_id} is not an unknown-licence Jev train row; nothing written")
        if not source or not target or source == target or not has_khmer(target) or has_khmer(source):
            raise SystemExit(f"{row_id} source or Khmer check failed; nothing written")
        if example.review_status == "gold":
            live_gold += 1
            approved = str(row.get("approved_text") or "").strip()
            if approved and approved != ranked:
                gold_differs += 1
        elif example.review_status == "pending_native_review":
            live_pending += 1
        else:
            raise SystemExit(f"{row_id} unexpected review_status; nothing written")
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
    if len(sft_rows) != 1000 or live_gold != 100 or live_pending != 900:
        raise SystemExit("SFT row composition is not 1000 train rows; nothing written")

    model_card = """# Spoken Khmer train export

1,000 stored Jev lines for ids kp-001–kp-1000. This file is not a trained language model. It is not promoted. The licence is unknown. Holdout ids kp-1001–kp-2000 are excluded. No weights were written.

| Field | Value |
| --- | --- |
| File | `sft-train-approved.jsonl` |
| Rows | 1000 |
| Ids | kp-001–kp-1000 |
| Split | train |
| Khmer line | stored Jev line |
| Licence | unknown |
| owner_training_approved | true |
| Owner grant | `data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000/` |
| External licence | none recorded. This grant is not CC-BY. |
| Promotion | not_promoted |
| Holdout | excluded. Holdout count in this file is 0. |
| Weights | none written, none uploaded |
| started | false |

`trainer.start` was not called. No 3B, 7B, 8B, or 14B fine-tune was started. The live `spoken_scale.jsonl` review fields were not changed. The open file `data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl` and `translate-sft-spoken-20261026-b/sft-train-approved.jsonl` were not rewritten.
"""

    sidecar_manifest = {
        "version": "owner-approval-sidecar-20261026-kp1000",
        "schema": "spoken-owner-approval-sidecar-1",
        "created_at": created,
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "training_started": False,
        "trainer_start_called": False,
        "fill_started": False,
        "promotion": "not_promoted",
        "hosted_fine_tune": "not_started",
        "vertex_fine_tune": "not_called",
        "licence": "unknown",
        "invented_external_licence": False,
        "not_gold": True,
        "native_gold_benchmark": False,
        "not_the_1000_to_2000_native_gold_benchmark": True,
        "newly_marked_gold": 0,
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "teacher": "gemini",
        "ranker": "jev",
        "gemini_and_jev_are_not_a_weight_update": True,
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "owner_quote": OWNER_QUOTE,
        "owner_quote_scope": (
            "Standing project-owner approval that training use is allowed while licence "
            "remains unknown. This sidecar records that approval for training-export use "
            "on train rows that were not already in an approval sidecar. It is not CC-BY, "
            "not a native-reviewer gold mark, and not a fine-tune launch."
        ),
        "why_sidecar": (
            "kp-101–kp-636 stay in the 20261023 sidecar. kp-637–kp-720 stay in the "
            "20261026 sidecar. kp-721–kp-733 stay in the 20261026-next sidecar. "
            "kp-001–kp-100 stay the existing gold rows and are not repeated here. "
            "The live file stays pending_native_review on the new rows."
        ),
        "live_jsonl_edited": False,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "snapshot_sha256": snapshot_sha,
        "snapshot_rows": 2000,
        "prior_sidecars_kept": [str(path.relative_to(ROOT)) for path in PRIOR_SIDECARS],
        "prior_sidecar_overwritten": False,
        "prior_sidecar_counts": prior_counts,
        "prior_version_kept": "data/khmer_spoken/versions/scale-lock1000-20261023",
        "locked_ids_unchanged": True,
        "locked_ids_sha256": locked_sha,
        "locked_ids_match_scale_lock": True,
        "split": {
            "rule": "last 1000 ids locked; earlier ids are the train pool",
            "train_count": 1000,
            "locked_count": 1000,
            "train_id_first": "kp-001",
            "train_id_last": "kp-1000",
            "locked_id_first": "kp-1001",
            "locked_id_last": "kp-2000",
            "train_on_locked": False,
            "tune_on_locked": False,
            "new_approvals_first": "kp-734",
            "new_approvals_last": "kp-1000",
            "new_approvals_count": 267,
            "new_approval_gaps": [],
            "holdout_approved": 0,
            "holdout_with_candidates": 0,
        },
        "approval": {
            "recorded_in": "approvals.jsonl",
            "applied_to_live_jsonl": False,
            "purpose": "training-export",
            "count": 267,
            "first_id": "kp-734",
            "last_id": "kp-1000",
            "review_status": "approved",
            "verified_by": "project-owner",
            "marked_gold": False,
            "empty_stubs_approved": 0,
            "holdout_approved": 0,
            "licence": "unknown",
            "prior_reviewer_notes_nonempty": sum(1 for row in approvals if row["prior_reviewer_notes"]),
            "history_kept": True,
            "skipped": {
                "already_in_prior_sidecar": 633,
                "already_approved_kp001_100": 100,
                "empty_stub": 0,
                "holdout": 0,
                "not_pending": 0,
                "licence_not_unknown": 0,
            },
        },
        "snapshot_counts": {
            "source_rows": 2000,
            "train_filled": 1000,
            "train_empty": 0,
            "holdout_filled": 0,
            "with_gemini_candidates_train": 1000,
            "jev_ranked_train": 1000,
            "last_id_with_candidates": "kp-1000",
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    grant_manifest = {
        "version": "owner-licence-grant-20261026-kp1000",
        "schema": "spoken-owner-licence-grant-1",
        "created_at": created,
        "statement": GRANT_STATEMENT,
        "owner_quote": OWNER_QUOTE,
        "owner_quote_scope": (
            "Standing project-owner approval that training use is allowed while licence "
            "remains unknown. This grant covers train ids kp-001–kp-1000 only. It is not "
            "an external licence. It does not change holdout rows, invent CC-BY, mark "
            "native gold, promote, call Vertex, or launch a 3B, 7B, 8B, or 14B fine-tune."
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
        "holdout_count": 0,
        "promotion": "not_promoted",
        "newly_marked_gold": 0,
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "trainer_start_called": False,
        "fill_started": False,
        "id_first": "kp-001",
        "id_last": "kp-1000",
        "id_range": "kp-001–kp-1000",
        "included_count": 1000,
        "included_ids_file": "data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000/train_ids.txt",
        "train_pool": "kp-001–kp-1000",
        "holdout": "kp-1001–kp-2000",
        "prior_grant_kept": "data/khmer_spoken/versions/owner-licence-grant-20261026",
        "prior_grant_overwritten": False,
        "prior_grant_included_count": line_count(PRIOR_GRANT / "grants.jsonl"),
        "train_pool_without_jev_excluded": 0,
        "excluded_non_unknown_licence": [],
        "gaps": [],
        "snapshot_sha256": snapshot_sha,
        "snapshot_rows": 2000,
        "snapshot_note": (
            "Train pool kp-001–kp-1000 each had Gemini candidates and a matching Jev line. "
            "Holdout kp-1001–kp-2000 had no candidates. The live file was not edited."
        ),
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    sft_manifest = {
        "version": "translate-sft-spoken-20261026-c",
        "schema": "spoken-translate-sft-approved-1",
        "created_at": created,
        "dry_run": True,
        "started": False,
        "training_started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "trainer_start_called": False,
        "fill_started": False,
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
        "licence_grant": "data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000",
        "licence_grant_statement": GRANT_STATEMENT,
        "approval_sidecar": "data/khmer_spoken/versions/owner-approval-sidecar-20261026-kp1000",
        "target_rule": (
            "DialogueExample.training_khmer(). The khmer field is the stored Jev line when "
            "it matches a candidate. Holdout ids are excluded. The open 720-line sft.jsonl "
            "and the 758-line sft-train-approved.jsonl were not rewritten."
        ),
        "prior_open_sft": "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl",
        "prior_open_sft_left_unmodified": True,
        "prior_open_sft_lines_before": 720,
        "prior_open_sft_sha256_before": open_sft_sha,
        "prior_approved_sft": (
            "data/khmer_spoken/versions/translate-sft-spoken-20261026-b/sft-train-approved.jsonl"
        ),
        "prior_approved_sft_left_unmodified": True,
        "prior_approved_sft_lines_before": 758,
        "prior_approved_sft_sha256_before": prior_sft_sha,
        "path": "data/khmer_spoken/versions/translate-sft-spoken-20261026-c/sft-train-approved.jsonl",
        "row_count": 1000,
        "id_first": "kp-001",
        "id_last": "kp-1000",
        "id_range": "kp-001–kp-1000",
        "split": "train",
        "fields": ["id", "source", "khmer", "licence", "owner_training_approved", "split"],
        "from_jev_count": 1000,
        "stub_used_count": 0,
        "holdout_excluded": True,
        "holdout_ids_in_export": 0,
        "holdout_filled": 0,
        "live_review_status_among_exported": {
            "gold": live_gold,
            "pending_native_review": live_pending,
        },
        "gold_approved_text_differs_from_jev": gold_differs,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "live_jsonl_edited": False,
        "snapshot_sha256": snapshot_sha,
        "snapshot_rows": 2000,
        "train_filled": 1000,
        "train_empty": 0,
        "gaps": [],
        "lock": {
            "version": "scale-lock1000-20261023",
            "train_id_first": "kp-001",
            "train_id_last": "kp-1000",
            "locked_id_first": "kp-1001",
            "locked_id_last": "kp-2000",
            "train_count": 1000,
            "locked_count": 1000,
            "locked_ids_sha256": locked_sha,
            "prior_directories_deleted": False,
        },
        "model_card": "data/khmer_spoken/versions/translate-sft-spoken-20261026-c/model-card.md",
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }

    try:
        SIDECAR_DIR.mkdir()
        GRANT_DIR.mkdir()
        SFT_DIR.mkdir()
        (SIDECAR_DIR / "approvals.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in approvals),
            encoding="utf-8",
        )
        (SIDECAR_DIR / "approval_ids.txt").write_text(
            "".join(f"{row_id}\n" for row_id in approval_ids),
            encoding="utf-8",
        )
        (SIDECAR_DIR / "locked_ids.txt").write_bytes(locked_bytes)
        (GRANT_DIR / "grants.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in grants),
            encoding="utf-8",
        )
        (GRANT_DIR / "train_ids.txt").write_text(
            "".join(f"{row_id}\n" for row_id in expected_train),
            encoding="utf-8",
        )
        sft_text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sft_rows)
        sft_path = SFT_DIR / "sft-train-approved.jsonl"
        sft_path.write_text(sft_text, encoding="utf-8")
        (SFT_DIR / "exported_ids.txt").write_text(
            "".join(f"{row_id}\n" for row_id in expected_train),
            encoding="utf-8",
        )
        (SFT_DIR / "model-card.md").write_text(model_card, encoding="utf-8")
        sft_manifest["sft_sha256"] = sha256_bytes(sft_text.encode("utf-8"))
        for directory, manifest in (
            (SIDECAR_DIR, sidecar_manifest),
            (GRANT_DIR, grant_manifest),
            (SFT_DIR, sft_manifest),
        ):
            (directory / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        after = WORKSPACE.read_bytes()
        if after != raw:
            raise SystemExit("spoken_scale.jsonl changed during the write")
        if sha256_file(OPEN_SFT) != open_sft_sha or line_count(OPEN_SFT) != 720:
            raise SystemExit("open sft.jsonl changed")
        if sha256_file(PRIOR_SFT) != prior_sft_sha or line_count(PRIOR_SFT) != 758:
            raise SystemExit("758-row SFT file changed")
        if sha256_file(SIDECAR_DIR / "locked_ids.txt") != locked_sha:
            raise SystemExit("copied locked ids do not match the scale lock")
        blob = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                SIDECAR_DIR / "approvals.jsonl",
                SIDECAR_DIR / "manifest.json",
                GRANT_DIR / "grants.jsonl",
                GRANT_DIR / "manifest.json",
                SFT_DIR / "sft-train-approved.jsonl",
                SFT_DIR / "manifest.json",
                SFT_DIR / "model-card.md",
            )
        )
        if any(marker in blob for marker in KEY_MARKERS):
            raise SystemExit("refusing output that contains a key-shaped marker")
        if fill_alive():
            raise SystemExit("fill_scale.py started during the freeze")
    except Exception:
        remove_new_dirs()
        raise

    print(json.dumps({
        "train_filled": 1000,
        "train_empty": 0,
        "holdout_filled": 0,
        "sidecar_count": len(approvals),
        "sidecar_first": approval_ids[0],
        "sidecar_last": approval_ids[-1],
        "grant_count": len(grants),
        "sft_count": len(sft_rows),
        "live_gold": live_gold,
        "live_pending": live_pending,
        "gold_approved_text_differs_from_jev": gold_differs,
        "snapshot_sha256": snapshot_sha,
        "sft_sha256": sft_manifest["sft_sha256"],
        "open_sft_sha256_unchanged": open_sft_sha,
        "prior_sft_sha256_unchanged": prior_sft_sha,
        "locked_ids_sha256": locked_sha,
        "started": False,
        "weights_written": False,
        "trainer_start_called": False,
        "fill_started": False,
        "live_jsonl_edited": False,
    }, indent=2))


if __name__ == "__main__":
    main()
