"""Package kp-2001–kp-2200 without editing live review fields.

Writes a new approval sidecar, a licence-use grant, and a 1,200-row
translation SFT export. Reads spoken_scale.jsonl and spoken_train_next.jsonl.
Does not write either file. Does not fill rows and does not call trainer.start.
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
SCALE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
NEXT = ROOT / "data/khmer_spoken/workspace/spoken_train_next.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
OPEN_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl"
PRIOR_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-b/sft-train-approved.jsonl"
C_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-c/sft-train-approved.jsonl"
PRIOR_GRANT = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000"
SIDECAR_DIR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261027-kp2200"
GRANT_DIR = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2200"
SFT_DIR = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261027-d"
OWNER_QUOTE = "if licence is still unknown i approve you do sometihnk and continue trained."
SESSION_QUOTE = "continue next"
GRANT_STATEMENT = (
    "The project owner approved training use of the listed spoken Khmer rows "
    "while license_type remains unknown. This grant covers kp-001–kp-1000 and "
    "kp-2001–kp-2200 only. It is not CC-BY and not any other external licence. "
    "Holdout rows kp-1001–kp-2000 are not included and were not changed."
)
KEY_MARKERS = ("AIza", "sk-", "hf_", "ghp_", "xoxb-", "api_key", "BEGIN PRIVATE")
FILL_TOKENS = ("fill_scale.py", "fill_next.py", "fill_kp")


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


def line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def has_candidate(row: dict) -> bool:
    return any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))


def candidate_count(row: dict) -> int:
    return sum(1 for cand in (row.get("candidates") or []) if str((cand or {}).get("text") or "").strip())


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


def read_stable(path: Path) -> tuple[bytes, list[dict]]:
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise SystemExit(f"{path.name} changed between two reads; nothing written")
    rows = [json.loads(line) for line in first.decode("utf-8").splitlines() if line.strip()]
    return first, rows


def fill_alive() -> str:
    proc = subprocess.run(["ps", "-ax", "-o", "args="], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("could not list processes; nothing written")
    hits = [line.strip() for line in proc.stdout.splitlines() if any(token in line for token in FILL_TOKENS)]
    return hits[0] if hits else ""


def remove_new_dirs() -> None:
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            shutil.rmtree(path)


def holdout_number(row_id: str) -> bool:
    number = kp_num(row_id)
    return 1001 <= number <= 2000


def main() -> None:
    running = fill_alive()
    if running:
        raise SystemExit(f"a fill process is running; nothing written: {running}")
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            raise SystemExit(f"refusing to overwrite {path}")
    for path in (OPEN_SFT, PRIOR_SFT, C_SFT, SCALE, NEXT, PRIOR_GRANT / "grants.jsonl"):
        if not path.is_file():
            raise SystemExit(f"missing {path}; nothing written")

    open_sft_sha = sha256_file(OPEN_SFT)
    prior_sft_sha = sha256_file(PRIOR_SFT)
    c_sft_sha = sha256_file(C_SFT)
    open_sft_lines = line_count(OPEN_SFT)
    prior_sft_lines = line_count(PRIOR_SFT)
    c_sft_lines = line_count(C_SFT)
    if open_sft_lines != 720 or prior_sft_lines != 758 or c_sft_lines != 1000:
        raise SystemExit(
            f"prior SFT line counts are {open_sft_lines}, {prior_sft_lines}, {c_sft_lines}; nothing written"
        )

    locked_ids = load_ids(LOCK / "locked_ids.txt")
    expected_locked = [f"kp-{index:03d}" for index in range(1001, 2001)]
    if locked_ids != expected_locked:
        raise SystemExit("scale lock is not holdout kp-1001–kp-2000")
    locked_bytes = (LOCK / "locked_ids.txt").read_bytes()
    locked_sha = sha256_bytes(locked_bytes)

    scale_raw, scale_rows = read_stable(SCALE)
    next_raw, next_rows = read_stable(NEXT)
    scale_sha = sha256_bytes(scale_raw)
    next_sha = sha256_bytes(next_raw)
    expected_scale = [f"kp-{index:03d}" for index in range(1, 2001)]
    expected_next = [f"kp-{index:04d}" for index in range(2001, 2201)]
    expected_train = expected_scale[:1000]
    if [row.get("id") for row in scale_rows] != expected_scale:
        raise SystemExit("spoken_scale ids are not kp-001–kp-2000; nothing written")
    if [row.get("id") for row in next_rows] != expected_next:
        raise SystemExit("spoken_train_next ids are not kp-2001–kp-2200; nothing written")

    scale_by_id = {row["id"]: row for row in scale_rows}
    holdout_filled = [
        row["id"]
        for row in scale_rows
        if holdout_number(row["id"]) and (has_candidate(row) or jev_text(row))
    ]
    train_filled = [
        row_id
        for row_id in expected_train
        if has_candidate(scale_by_id[row_id]) and jev_text(scale_by_id[row_id])
    ]
    if holdout_filled or train_filled != expected_train:
        raise SystemExit(
            "scale counts are not train_filled 1000 and holdout_filled 0: "
            f"train_filled={len(train_filled)} holdout_filled={len(holdout_filled)}; nothing written"
        )

    c_rows = [json.loads(line) for line in C_SFT.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row.get("id") for row in c_rows] != expected_train:
        raise SystemExit("the -c export is not kp-001–kp-1000; nothing written")

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sft_rows: list[dict] = []
    grants: list[dict] = []
    for c_row, row_id in zip(c_rows, expected_train, strict=True):
        live = scale_by_id[row_id]
        ranked = jev_text(live)
        example = DialogueExample.from_dict(live)
        if c_row.get("source") != example.source_text.strip():
            raise SystemExit(f"{row_id} -c source does not match the live source; nothing written")
        if c_row.get("khmer") != ranked or example.training_khmer().strip() != ranked:
            raise SystemExit(f"{row_id} -c Khmer is not the stored Jev line; nothing written")
        if c_row.get("licence") != "unknown" or example.license_type != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown; nothing written")
        if c_row.get("owner_training_approved") is not True or c_row.get("split") != "train":
            raise SystemExit(f"{row_id} -c approval fields are unexpected; nothing written")
        if not has_khmer(ranked) or has_khmer(example.source_text):
            raise SystemExit(f"{row_id} script check failed; nothing written")
        sft_rows.append({
            "id": row_id,
            "source": c_row["source"],
            "khmer": c_row["khmer"],
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
            "source_file": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        })

    approvals: list[dict] = []
    for row in next_rows:
        row_id = row["id"]
        if holdout_number(row_id):
            raise SystemExit(f"{row_id} is a holdout id; nothing written")
        if str(row.get("review_status") or "") != "pending_native_review":
            raise SystemExit(f"{row_id} is not pending_native_review; nothing written")
        if str(row.get("license_type") or "") != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown; nothing written")
        if row.get("verified_by") or str(row.get("approved_text") or "").strip():
            raise SystemExit(f"{row_id} already has a live approval; nothing written")
        if row.get("origin") != "gemini_teacher":
            raise SystemExit(f"{row_id} origin is not gemini_teacher; nothing written")
        if candidate_count(row) != 3:
            raise SystemExit(f"{row_id} does not have 3 candidates; nothing written")
        ranked = jev_text(row)
        example = DialogueExample.from_dict(row)
        if example.training_khmer().strip() != ranked or not ranked or not has_khmer(ranked):
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
            "origin": "gemini_teacher",
            "approved_text": ranked,
            "candidate_count": 3,
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
            "session_quote": SESSION_QUOTE,
            "by": "project-owner",
            "live_file_edited": False,
            "split": "train",
            "source_file": "data/khmer_spoken/workspace/spoken_train_next.jsonl",
        })
        sft_rows.append({
            "id": row_id,
            "source": source,
            "khmer": ranked,
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
            "session_quote": SESSION_QUOTE,
            "by": "project-owner",
            "source_file": "data/khmer_spoken/workspace/spoken_train_next.jsonl",
        })

    approval_ids = [row["id"] for row in approvals]
    grant_ids = [row["id"] for row in grants]
    sft_ids = [row["id"] for row in sft_rows]
    expected_grant = expected_train + expected_next
    if approval_ids != expected_next or grant_ids != expected_grant or sft_ids != expected_grant:
        raise SystemExit("packaged ids are not kp-001–kp-1000 plus kp-2001–kp-2200; nothing written")
    if any(holdout_number(row_id) for row_id in sft_ids):
        raise SystemExit("holdout id in the export; nothing written")
    if len(sft_rows) != 1200 or len(grants) != 1200 or len(approvals) != 200:
        raise SystemExit("counts are not sidecar 200, grant 1200, sft 1200; nothing written")

    model_card = """# Spoken Khmer train export

1,200 stored Jev lines. Ids kp-001–kp-1000 come from the frozen 20261026-c export. Ids kp-2001–kp-2200 come from the stored Jev lines in spoken_train_next.jsonl. This file is not a trained language model. It is not promoted. The licence is unknown. Holdout ids kp-1001–kp-2000 are excluded. No weights were written.

| Field | Value |
| --- | --- |
| File | `sft-train-approved.jsonl` |
| Rows | 1200 |
| Ids | kp-001–kp-1000 and kp-2001–kp-2200 |
| Split | train |
| Khmer line | stored Jev line |
| Licence | unknown |
| owner_training_approved | true |
| Owner grant | `data/khmer_spoken/versions/owner-licence-grant-20261027-kp2200/` |
| External licence | none recorded. This grant is not CC-BY. |
| Promotion | not_promoted |
| Holdout | excluded. Holdout count in this file is 0. |
| Weights | none written, none uploaded |
| started | false |

`trainer.start` was not called. No 3B, 7B, 8B, or 14B fine-tune was started. Live review fields in `spoken_scale.jsonl` and `spoken_train_next.jsonl` were not changed. The open file `translate-sft-spoken-20261026/sft.jsonl`, the 758-row export, and the 1,000-row -c export were not rewritten.
"""

    sidecar_manifest = {
        "version": "owner-approval-sidecar-20261027-kp2200",
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
        "session_quote": SESSION_QUOTE,
        "owner_quote_scope": (
            "Standing project-owner approval that training use is allowed while licence "
            "remains unknown. This sidecar records that approval for training-export use "
            "on kp-2001–kp-2200 only. It is not CC-BY, not a native-reviewer gold mark, "
            "and not a fine-tune launch."
        ),
        "why_sidecar": (
            "kp-2001–kp-2200 live in spoken_train_next.jsonl and stay pending_native_review "
            "there. Earlier train-pool approvals stay in the prior sidecars. Holdout "
            "kp-1001–kp-2000 is not approved."
        ),
        "live_jsonl_edited": False,
        "live_files": [
            "data/khmer_spoken/workspace/spoken_scale.jsonl",
            "data/khmer_spoken/workspace/spoken_train_next.jsonl",
        ],
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "snapshot_rows_scale": 2000,
        "snapshot_rows_train_next": 200,
        "prior_version_kept": "data/khmer_spoken/versions/scale-lock1000-20261023",
        "locked_ids_unchanged": True,
        "locked_ids_sha256": locked_sha,
        "locked_ids_match_scale_lock": True,
        "split": {
            "rule": "holdout kp-1001–kp-2000 stays locked; this sidecar is kp-2001–kp-2200",
            "new_approvals_first": "kp-2001",
            "new_approvals_last": "kp-2200",
            "new_approvals_count": 200,
            "new_approval_gaps": [],
            "holdout_approved": 0,
            "holdout_with_candidates": 0,
            "train_on_locked": False,
            "tune_on_locked": False,
        },
        "approval": {
            "recorded_in": "approvals.jsonl",
            "applied_to_live_jsonl": False,
            "purpose": "training-export",
            "count": 200,
            "first_id": "kp-2001",
            "last_id": "kp-2200",
            "review_status": "approved",
            "verified_by": "project-owner",
            "marked_gold": False,
            "empty_stubs_approved": 0,
            "holdout_approved": 0,
            "licence": "unknown",
            "prior_reviewer_notes_nonempty": sum(1 for row in approvals if row["prior_reviewer_notes"]),
            "history_kept": True,
            "live_review_status_left": "pending_native_review",
        },
        "snapshot_counts": {
            "train_next_rows": 200,
            "train_next_filled": 200,
            "train_next_empty": 0,
            "candidates_each": 3,
            "jev_ranked": 200,
            "holdout_filled": 0,
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    grant_manifest = {
        "version": "owner-licence-grant-20261027-kp2200",
        "schema": "spoken-owner-licence-grant-1",
        "created_at": created,
        "statement": GRANT_STATEMENT,
        "owner_quote": OWNER_QUOTE,
        "session_quote": SESSION_QUOTE,
        "owner_quote_scope": (
            "Standing project-owner approval that training use is allowed while licence "
            "remains unknown. This grant covers kp-001–kp-1000 and kp-2001–kp-2200 only. "
            "It is not an external licence. It does not change holdout rows, invent CC-BY, "
            "mark native gold, promote, call Vertex, or launch a 3B, 7B, 8B, or 14B fine-tune."
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
        "live_files": [
            "data/khmer_spoken/workspace/spoken_scale.jsonl",
            "data/khmer_spoken/workspace/spoken_train_next.jsonl",
        ],
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
        "id_ranges": ["kp-001–kp-1000", "kp-2001–kp-2200"],
        "included_count": 1200,
        "included_ids_file": "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2200/train_ids.txt",
        "excluded_holdout": "kp-1001–kp-2000",
        "prior_grant_kept": "data/khmer_spoken/versions/owner-licence-grant-20261026-kp1000",
        "prior_grant_overwritten": False,
        "prior_grant_included_count": line_count(PRIOR_GRANT / "grants.jsonl"),
        "gaps_are_holdout_only": True,
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "snapshot_note": (
            "kp-001–kp-1000 keep the Jev lines already frozen in the -c export. "
            "kp-2001–kp-2200 each had three Gemini candidates and a matching Jev line. "
            "Holdout kp-1001–kp-2000 had no candidates. Neither live file was edited."
        ),
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    sft_manifest = {
        "version": "translate-sft-spoken-20261027-d",
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
        "session_quote": SESSION_QUOTE,
        "licence_grant": "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2200",
        "licence_grant_statement": GRANT_STATEMENT,
        "approval_sidecar": "data/khmer_spoken/versions/owner-approval-sidecar-20261027-kp2200",
        "target_rule": (
            "The first 1000 khmer fields are copied from translate-sft-spoken-20261026-c "
            "and match that file's stored Jev lines. The next 200 khmer fields are the "
            "stored Jev lines from spoken_train_next.jsonl. Holdout ids are excluded."
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
        "prior_c_sft": (
            "data/khmer_spoken/versions/translate-sft-spoken-20261026-c/sft-train-approved.jsonl"
        ),
        "prior_c_sft_left_unmodified": True,
        "prior_c_sft_lines_before": 1000,
        "prior_c_sft_sha256_before": c_sft_sha,
        "path": "data/khmer_spoken/versions/translate-sft-spoken-20261027-d/sft-train-approved.jsonl",
        "row_count": 1200,
        "from_c_export": 1000,
        "from_train_next_jev": 200,
        "id_ranges": ["kp-001–kp-1000", "kp-2001–kp-2200"],
        "id_first": "kp-001",
        "id_last": "kp-2200",
        "split": "train",
        "fields": ["id", "source", "khmer", "licence", "owner_training_approved", "split"],
        "from_jev_count": 1200,
        "stub_used_count": 0,
        "holdout_excluded": True,
        "holdout_ids_in_export": 0,
        "holdout_filled": 0,
        "started_flag": False,
        "live_jsonl_edited": False,
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "lock": {
            "version": "scale-lock1000-20261023",
            "locked_id_first": "kp-1001",
            "locked_id_last": "kp-2000",
            "locked_count": 1000,
            "locked_ids_sha256": locked_sha,
            "prior_directories_deleted": False,
        },
        "model_card": "data/khmer_spoken/versions/translate-sft-spoken-20261027-d/model-card.md",
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
            "".join(f"{row_id}\n" for row_id in grant_ids),
            encoding="utf-8",
        )
        sft_text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sft_rows)
        (SFT_DIR / "sft-train-approved.jsonl").write_text(sft_text, encoding="utf-8")
        (SFT_DIR / "exported_ids.txt").write_text(
            "".join(f"{row_id}\n" for row_id in sft_ids),
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

        if SCALE.read_bytes() != scale_raw or NEXT.read_bytes() != next_raw:
            raise SystemExit("a live jsonl changed during the write")
        if sha256_file(OPEN_SFT) != open_sft_sha or line_count(OPEN_SFT) != 720:
            raise SystemExit("open sft.jsonl changed")
        if sha256_file(PRIOR_SFT) != prior_sft_sha or line_count(PRIOR_SFT) != 758:
            raise SystemExit("758-row SFT file changed")
        if sha256_file(C_SFT) != c_sft_sha or line_count(C_SFT) != 1000:
            raise SystemExit("1000-row -c SFT file changed")
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
            raise SystemExit("a fill process appeared during the package")
    except Exception:
        remove_new_dirs()
        raise

    print(json.dumps({
        "train_next_filled": 200,
        "holdout_filled": 0,
        "sidecar_count": 200,
        "sidecar_first": "kp-2001",
        "sidecar_last": "kp-2200",
        "grant_count": 1200,
        "sft_count": 1200,
        "from_c_export": 1000,
        "from_train_next_jev": 200,
        "holdout_ids_in_export": 0,
        "started": False,
        "weights_written": False,
        "trainer_start_called": False,
        "fill_started": False,
        "live_jsonl_edited": False,
        "scale_sha256_unchanged": scale_sha,
        "train_next_sha256_unchanged": next_sha,
        "open_sft_sha256_unchanged": open_sft_sha,
        "prior_b_sha256_unchanged": prior_sft_sha,
        "prior_c_sha256_unchanged": c_sft_sha,
        "sft_sha256": sft_manifest["sft_sha256"],
        "locked_ids_sha256": locked_sha,
    }, indent=2))


if __name__ == "__main__":
    main()
