"""Snapshot spoken_scale and write a translation SFT export plus an approval sidecar.

Does not edit spoken_scale.jsonl, the scale lock, or older version directories.
Does not start training.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.khmer_spoken.schema import DialogueExample
from claynext.models.training.trainer import training_implementation_available

ROOT = Path(__file__).resolve().parents[4]
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
PRIOR_SIDECAR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261023"
SFT_DIR = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026"
SIDECAR_DIR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026"
OWNER_QUOTE = "next translate train spoke khmer."


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def kp_num(row_id: str) -> int:
    tail = str(row_id).split("-", 1)[-1]
    if not tail.isdigit():
        raise SystemExit(f"bad id {row_id}")
    return int(tail)


def has_khmer(text: str) -> bool:
    return any("\u1780" <= ch <= "\u17ff" for ch in text)


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


def load_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if any(path.exists() for path in (SFT_DIR, SIDECAR_DIR)):
        raise SystemExit("refusing to overwrite an existing 20261026 version directory")
    before = sha256_file(WORKSPACE)
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
    if set(train_ids) & set(locked_ids):
        raise SystemExit("train and holdout ids overlap")

    raw = WORKSPACE.read_text(encoding="utf-8")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    ids = [row.get("id") for row in rows]
    if ids != [f"kp-{index:03d}" for index in range(1, len(rows) + 1)]:
        raise SystemExit("spoken_scale ids are not contiguous from kp-001")
    by_id = {row["id"]: row for row in rows}

    prior_approved = set(load_ids(PRIOR_SIDECAR / "approval_ids.txt"))
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sft_lines: list[str] = []
    exported_ids: list[str] = []
    approvals: list[dict] = []
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
        stub = example.stub_khmer.strip()
        if stub and target == stub and target != ranked:
            raise SystemExit(f"{row_id} used the stub")
        if not source or not target or source == target:
            raise SystemExit(f"{row_id} source or target is empty or identical")
        if not has_khmer(target) or has_khmer(source):
            raise SystemExit(f"{row_id} source/target script check failed")
        if example.license_type != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown")
        if row_id in locked_ids or kp_num(row_id) > 1000:
            raise SystemExit(f"{row_id} is holdout")
        approved = str(row.get("approved_text") or "").strip()
        if example.review_status == "gold":
            live_gold += 1
            if approved and approved != ranked:
                gold_differs += 1
        elif example.review_status == "pending_native_review":
            live_pending += 1
        else:
            raise SystemExit(f"{row_id} unexpected review_status {example.review_status}")
        sft_lines.append(json.dumps({
            "id": row_id,
            "source": source,
            "target": target,
            "licence": "unknown",
            "split": "train",
            "from_jev": True,
        }, ensure_ascii=False))
        exported_ids.append(row_id)

        if row_id in prior_approved or example.review_status != "pending_native_review":
            continue
        if row.get("verified_by") or approved:
            continue
        if not has_candidate(row):
            continue
        candidates = row.get("candidates") or []
        provider = ""
        if candidates and isinstance(candidates[0], dict):
            provider = str(candidates[0].get("provider") or "")
        jev = (row.get("metadata") or {}).get("jev") or {}
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
            "approved_text": target,
            "candidate_count": len(candidates),
            "candidate_provider": provider,
            "jev_applied": True,
            "jev_preferred_index": jev.get("preferred_index"),
            "not_gold": True,
            "not_for_weight_training": True,
            "promotion": "not_promoted",
            "quote": OWNER_QUOTE,
            "by": "project-owner",
            "live_file_edited": False,
            "split": "train",
        })

    holdout_with_candidates = [
        row["id"] for row in rows if row["id"] in set(locked_ids) and has_candidate(row)
    ]
    if holdout_with_candidates:
        raise SystemExit("holdout rows have candidates; export aborted")
    if any(row_id in set(locked_ids) for row_id in exported_ids):
        raise SystemExit("export contains a holdout id")
    empty_train = [
        row_id for row_id in train_ids
        if not has_candidate(by_id[row_id])
    ]
    cand_ids = [row["id"] for row in rows if has_candidate(row)]
    last_cand = cand_ids[-1] if cand_ids else ""
    if exported_ids != [f"kp-{index:03d}" for index in range(1, len(exported_ids) + 1)]:
        raise SystemExit("exported ids have a gap or do not start at kp-001")

    SFT_DIR.mkdir(parents=True)
    SIDECAR_DIR.mkdir(parents=True)
    sft_path = SFT_DIR / "sft.jsonl"
    sft_path.write_text("".join(line + "\n" for line in sft_lines), encoding="utf-8")
    (SFT_DIR / "exported_ids.txt").write_text("".join(f"{row_id}\n" for row_id in exported_ids), encoding="utf-8")
    (SIDECAR_DIR / "approvals.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in approvals),
        encoding="utf-8",
    )
    (SIDECAR_DIR / "approval_ids.txt").write_text(
        "".join(f"{row['id']}\n" for row in approvals),
        encoding="utf-8",
    )
    (SIDECAR_DIR / "locked_ids.txt").write_bytes((LOCK / "locked_ids.txt").read_bytes())
    if sha256_file(SIDECAR_DIR / "locked_ids.txt") != lock_hashes["locked_ids.txt"]:
        raise SystemExit("copied locked ids do not match the scale lock")

    trainer_installed = training_implementation_available()
    sft_manifest = {
        "version": "translate-sft-spoken-20261026",
        "schema": "spoken-translate-sft-1",
        "created_at": created,
        "dry_run": True,
        "started": False,
        "training_started": False,
        "trainer_start_called": False,
        "weights_written": False,
        "weights_uploaded": False,
        "trainer_installed": trainer_installed,
        "promotion": "not_promoted",
        "hosted_fine_tune": "not_started",
        "vertex_fine_tune": "not_called",
        "licence": "unknown",
        "invented_external_licence": False,
        "native_gold_benchmark": False,
        "not_the_1000_to_2000_native_gold_benchmark": True,
        "newly_marked_gold": 0,
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "teacher": "gemini",
        "ranker": "jev",
        "gemini_and_jev_are_not_a_weight_update": True,
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "blocked_reason": "16 GB M4. trainer.start was not called and was not changed.",
        "owner_quote": OWNER_QUOTE,
        "owner_quote_scope": (
            "Build a translation SFT export from train-pool rows that already have a Jev Khmer line, "
            "and record owner approval on newly filled train rows. Not approval to train 3B, 7B, 8B, "
            "or 14B weights, call Vertex, invent a licence, or mark synthetic rows as native gold."
        ),
        "target_rule": (
            "DialogueExample.training_khmer(). The Jev preferred line is the target when it matches "
            "a candidate. The stub is not used. export_ranked_training drops pending_native_review, "
            "and those rows stay pending in spoken_scale.jsonl so a later fill can resume."
        ),
        "path": "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl",
        "row_count": len(exported_ids),
        "id_first": exported_ids[0] if exported_ids else "",
        "id_last": exported_ids[-1] if exported_ids else "",
        "split": "train",
        "from_jev_count": len(exported_ids),
        "stub_used_count": 0,
        "holdout_excluded": True,
        "holdout_ids_in_export": 0,
        "holdout_with_candidates_at_snapshot": 0,
        "live_review_status": {"gold": live_gold, "pending_native_review": live_pending},
        "gold_approved_text_differs_from_jev": gold_differs,
        "prior_sidecar": "data/khmer_spoken/versions/owner-approval-sidecar-20261023",
        "prior_sidecar_approvals": len(prior_approved),
        "new_sidecar": "data/khmer_spoken/versions/owner-approval-sidecar-20261026",
        "new_sidecar_approvals": len(approvals),
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "live_jsonl_edited": False,
        "snapshot_sha256": before,
        "snapshot_rows": len(rows),
        "with_candidates": len(cand_ids),
        "jev_ranked_matching_candidate": len(cand_ids),
        "last_id_with_candidates": last_cand,
        "next_empty_id": empty_train[0] if empty_train else "",
        "train_pool_empty": len(empty_train),
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
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
    }
    (SFT_DIR / "manifest.json").write_text(
        json.dumps(sft_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    sidecar_manifest = {
        "version": "owner-approval-sidecar-20261026",
        "schema": "spoken-owner-approval-sidecar-1",
        "created_at": created,
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "training_started": False,
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
            "Continue the spoken dataset pipeline. Record owner approval on newly filled "
            "train-pool rows that already have Gemini candidates and a Jev rank. Not approval "
            "to train weights, invent a licence, mark native gold, or score the set."
        ),
        "why_sidecar": (
            "fill_scale.py refuses rows past kp-100 that are no longer pending_native_review. "
            "The live file was not edited. kp-101–kp-636 stay in the 20261023 sidecar."
        ),
        "live_jsonl_edited": False,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "snapshot_sha256": before,
        "snapshot_rows": len(rows),
        "prior_sidecar_kept": "data/khmer_spoken/versions/owner-approval-sidecar-20261023",
        "prior_sidecar_overwritten": False,
        "prior_version_kept": "data/khmer_spoken/versions/scale-lock1000-20261023",
        "locked_ids_unchanged": True,
        "locked_ids_sha256": lock_hashes["locked_ids.txt"],
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
            "new_approvals_first": approvals[0]["id"] if approvals else "",
            "new_approvals_last": approvals[-1]["id"] if approvals else "",
            "new_approvals_count": len(approvals),
            "holdout_approved": 0,
            "holdout_with_candidates": 0,
        },
        "approval": {
            "recorded_in": "approvals.jsonl",
            "applied_to_live_jsonl": False,
            "count": len(approvals),
            "first_id": approvals[0]["id"] if approvals else "",
            "last_id": approvals[-1]["id"] if approvals else "",
            "review_status": "approved",
            "verified_by": "project-owner",
            "marked_gold": False,
            "empty_stubs_approved": 0,
            "holdout_approved": 0,
            "licence": "unknown",
            "already_recorded_in_prior_sidecar": len(prior_approved),
        },
        "snapshot_counts": {
            "source_rows": len(rows),
            "with_candidates": len(cand_ids),
            "jev_ranked_matching_candidate": sum(1 for row in rows if jev_text(row)),
            "last_id_with_candidates": last_cand,
            "next_empty_id": empty_train[0] if empty_train else "",
            "train_pool_empty": len(empty_train),
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
    }
    (SIDECAR_DIR / "manifest.json").write_text(
        json.dumps(sidecar_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    after = sha256_file(WORKSPACE)
    if after != before:
        raise SystemExit("spoken_scale.jsonl changed while the export was written")
    if sha256_file(LOCK / "locked_ids.txt") != lock_hashes["locked_ids.txt"]:
        raise SystemExit("scale lock changed while the export was written")
    print(json.dumps({
        "sft_rows": len(exported_ids),
        "sft_first": exported_ids[0] if exported_ids else "",
        "sft_last": exported_ids[-1] if exported_ids else "",
        "sidecar_approvals": len(approvals),
        "sidecar_first": approvals[0]["id"] if approvals else "",
        "sidecar_last": approvals[-1]["id"] if approvals else "",
        "live_gold": live_gold,
        "live_pending": live_pending,
        "gold_differs_from_jev": gold_differs,
        "train_pool_empty": len(empty_train),
        "next_empty": empty_train[0] if empty_train else "",
        "last_cand": last_cand,
        "with_candidates": len(cand_ids),
        "holdout_with_candidates": 0,
        "trainer_installed": trainer_installed,
        "started": False,
        "weights_written": False,
        "live_jsonl_edited": False,
        "snapshot_sha256": before,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
