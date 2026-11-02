"""Record the next owner-approval sidecar from one read of spoken_scale.jsonl.

Does not write spoken_scale.jsonl. Does not start a fill or a trainer.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.khmer_spoken.schema import DialogueExample

ROOT = Path(__file__).resolve().parents[4]
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
PRIOR_SIDECARS = (
    ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261023",
    ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026",
)
SIDECAR_DIR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261026-next"
OWNER_QUOTE = "approvals next."
FILL_PID = 58618


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


def gemini_texts(row: dict) -> list[str]:
    texts: list[str] = []
    for cand in row.get("candidates") or []:
        if not isinstance(cand, dict):
            continue
        text = str(cand.get("text") or "").strip()
        provider = str(cand.get("provider") or "")
        if text and provider == "gemini_teacher":
            texts.append(text)
    return texts


def jev_match(row: dict, texts: list[str]) -> tuple[str, bool, object]:
    """Return (preferred text, applied, index). Empty text means no usable Jev line."""
    jev = (row.get("metadata") or {}).get("jev") or {}
    if not isinstance(jev, dict) or not jev:
        return "", False, None
    text = str(jev.get("preferred_text") or "").strip()
    applied = bool(jev.get("applied"))
    if not applied and not text:
        return "", False, None
    if applied and text and text in texts:
        return text, True, jev.get("preferred_index")
    raise SystemExit(f"{row.get('id')} has a Jev line that does not match a Gemini candidate")


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def main() -> None:
    if SIDECAR_DIR.exists():
        raise SystemExit(f"refusing to overwrite {SIDECAR_DIR}")
    for prior in PRIOR_SIDECARS:
        if not (prior / "approval_ids.txt").is_file():
            raise SystemExit(f"missing prior sidecar {prior}")

    lock_ids_hash = sha256_file(LOCK / "locked_ids.txt")
    locked_ids = load_ids(LOCK / "locked_ids.txt")
    train_ids = load_ids(LOCK / "train_ids.txt")
    expected_train = [f"kp-{index:03d}" for index in range(1, 1001)]
    expected_locked = [f"kp-{index:03d}" for index in range(1001, 2001)]
    if train_ids != expected_train or locked_ids != expected_locked:
        raise SystemExit("scale lock on disk is not train kp-001–kp-1000 and holdout kp-1001–kp-2000")

    snapshot = WORKSPACE.read_bytes()
    snapshot_sha = sha256_bytes(snapshot)
    raw = snapshot.decode("utf-8")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    ids = [row.get("id") for row in rows]
    if ids != [f"kp-{index:03d}" for index in range(1, len(rows) + 1)]:
        raise SystemExit("spoken_scale ids are not contiguous from kp-001")
    if len(rows) != 2000:
        raise SystemExit(f"expected 2000 rows, found {len(rows)}")

    prior_approved: set[str] = set()
    prior_counts: dict[str, int] = {}
    for prior in PRIOR_SIDECARS:
        found = load_ids(prior / "approval_ids.txt")
        prior_counts[prior.name] = len(found)
        overlap = prior_approved & set(found)
        if overlap:
            raise SystemExit(f"prior sidecars overlap on {sorted(overlap)[:5]}")
        prior_approved.update(found)

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    approvals: list[dict] = []
    skipped = {
        "already_in_prior_sidecar": 0,
        "already_approved_kp001_100": 0,
        "empty_stub": 0,
        "holdout": 0,
        "not_pending": 0,
        "licence_not_unknown": 0,
        "inflight_without_jev": 0,
        "no_khmer_candidate": 0,
    }
    holdout_with_candidates = 0
    with_candidates = 0
    jev_ranked = 0
    cand_ids: list[str] = []
    notes_kept = 0

    candidate_rows = [row for row in rows if gemini_texts(row)]
    newest_id = candidate_rows[-1]["id"] if candidate_rows else ""

    for row in rows:
        row_id = str(row.get("id") or "")
        number = kp_num(row_id)
        texts = gemini_texts(row)
        if texts:
            with_candidates += 1
            cand_ids.append(row_id)
        if number > 1000:
            if texts:
                holdout_with_candidates += 1
                skipped["holdout"] += 1
            continue
        if not texts:
            if number >= 721:
                skipped["empty_stub"] += 1
            continue
        if row_id in prior_approved:
            skipped["already_in_prior_sidecar"] += 1
            continue
        if number <= 100:
            skipped["already_approved_kp001_100"] += 1
            continue
        if str(row.get("license_type") or "") != "unknown":
            skipped["licence_not_unknown"] += 1
            continue
        status = str(row.get("review_status") or "")
        if status != "pending_native_review":
            skipped["not_pending"] += 1
            continue
        if row.get("verified_by") or str(row.get("approved_text") or "").strip():
            skipped["not_pending"] += 1
            continue
        jev_text, jev_applied, jev_index = jev_match(row, texts)
        if jev_applied:
            jev_ranked += 1
            target = jev_text
        elif row_id == newest_id and pid_alive(FILL_PID):
            skipped["inflight_without_jev"] += 1
            continue
        else:
            target = next((text for text in texts if has_khmer(text)), "")
        if not target or not has_khmer(target):
            skipped["no_khmer_candidate"] += 1
            continue
        example = DialogueExample.from_dict(row)
        if jev_applied and example.training_khmer().strip() != target:
            raise SystemExit(f"{row_id} training_khmer did not keep the Jev line")
        source = example.source_text.strip()
        if not source or source == target or has_khmer(source):
            raise SystemExit(f"{row_id} source check failed")
        if number > 1000 or row_id in set(locked_ids):
            raise SystemExit(f"{row_id} is holdout")
        prior_notes = str(row.get("reviewer_notes") or "")
        if prior_notes:
            notes_kept += 1
        candidates = row.get("candidates") or []
        approvals.append({
            "id": row_id,
            "decision": "approve",
            "from_status": status,
            "review_status": "approved",
            "verified_by": "project-owner",
            "verified_at": created,
            "license_type": "unknown",
            "invented_external_licence": False,
            "origin": row.get("origin") or "",
            "approved_text": target,
            "candidate_count": len([cand for cand in candidates if str((cand or {}).get("text") or "").strip()]),
            "candidate_provider": "gemini_teacher",
            "jev_applied": jev_applied,
            "jev_preferred_index": jev_index,
            "prior_reviewer_notes": prior_notes,
            "prior_review_status": status,
            "history_kept": True,
            "not_gold": True,
            "not_for_weight_training": True,
            "promotion": "not_promoted",
            "quote": OWNER_QUOTE,
            "by": "project-owner",
            "live_file_edited": False,
            "split": "train",
        })

    if not approvals:
        raise SystemExit("no new train-pool rows with Gemini candidates; sidecar not written")
    approval_ids = [row["id"] for row in approvals]
    if approval_ids != sorted(approval_ids, key=kp_num):
        raise SystemExit("approval ids are not in order")
    if set(approval_ids) & prior_approved:
        raise SystemExit("new approvals overlap a prior sidecar")
    if any(kp_num(row_id) <= 100 or kp_num(row_id) > 1000 for row_id in approval_ids):
        raise SystemExit("approval id is outside kp-101–kp-1000")
    numbers = [kp_num(row_id) for row_id in approval_ids]
    gaps = [f"kp-{index:03d}" for index in range(numbers[0], numbers[-1] + 1) if index not in set(numbers)]

    SIDECAR_DIR.mkdir(parents=True)
    (SIDECAR_DIR / "approvals.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in approvals),
        encoding="utf-8",
    )
    (SIDECAR_DIR / "approval_ids.txt").write_text(
        "".join(f"{row_id}\n" for row_id in approval_ids),
        encoding="utf-8",
    )
    (SIDECAR_DIR / "locked_ids.txt").write_bytes((LOCK / "locked_ids.txt").read_bytes())
    if sha256_file(SIDECAR_DIR / "locked_ids.txt") != lock_ids_hash:
        raise SystemExit("copied locked ids do not match the scale lock")

    after_sha = sha256_file(WORKSPACE)
    empty_train = [
        f"kp-{index:03d}" for index in range(1, 1001)
        if f"kp-{index:03d}" not in set(cand_ids)
    ]
    manifest = {
        "version": SIDECAR_DIR.name,
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
        "scores": {
            "chrf": "not_measured",
            "comet": "not_measured",
            "human": "not_measured",
        },
        "teacher": "gemini",
        "ranker": "jev",
        "gemini_and_jev_are_not_a_weight_update": True,
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "owner_quote": OWNER_QUOTE,
        "owner_quote_scope": (
            "Continue the spoken dataset pipeline. Record owner approval on the next "
            "train-pool rows that already have Gemini candidates and are not in the "
            "20261023 or 20261026 sidecars. A Jev line is the approved text when it "
            "matches a candidate. Not approval to train weights, invent a licence, "
            "mark native gold, change promotion, or score the set."
        ),
        "why_sidecar": (
            "fill_scale.py pid 58618 is rewriting spoken_scale.jsonl with atomic replace "
            "after each row and refuses rows past kp-100 that are no longer pending. "
            "The live file was not edited. kp-101–kp-636 stay in the 20261023 sidecar. "
            "kp-637–kp-720 stay in the 20261026 sidecar."
        ),
        "live_jsonl_edited": False,
        "live_jsonl_edited_by_this_process": False,
        "live_jsonl": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "snapshot_sha256": snapshot_sha,
        "workspace_sha256_after_sidecar_write": after_sha,
        "workspace_changed_after_snapshot": after_sha != snapshot_sha,
        "snapshot_rows": len(rows),
        "prior_sidecars_kept": [str(path.relative_to(ROOT)) for path in PRIOR_SIDECARS],
        "prior_sidecar_overwritten": False,
        "prior_sidecar_counts": prior_counts,
        "prior_version_kept": "data/khmer_spoken/versions/scale-lock1000-20261023",
        "locked_ids_unchanged": True,
        "locked_ids_sha256": lock_ids_hash,
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
            "new_approvals_first": approval_ids[0],
            "new_approvals_last": approval_ids[-1],
            "new_approvals_count": len(approvals),
            "new_approval_gaps": gaps,
            "holdout_approved": 0,
            "holdout_with_candidates": holdout_with_candidates,
        },
        "approval": {
            "recorded_in": "approvals.jsonl",
            "applied_to_live_jsonl": False,
            "count": len(approvals),
            "first_id": approval_ids[0],
            "last_id": approval_ids[-1],
            "review_status": "approved",
            "verified_by": "project-owner",
            "marked_gold": False,
            "empty_stubs_approved": 0,
            "holdout_approved": 0,
            "licence": "unknown",
            "prior_reviewer_notes_nonempty": notes_kept,
            "history_kept": True,
            "skipped": skipped,
            "already_recorded_in_prior_sidecars": len(prior_approved),
        },
        "snapshot_counts": {
            "source_rows": len(rows),
            "with_gemini_candidates": with_candidates,
            "last_id_with_candidates": cand_ids[-1] if cand_ids else "",
            "next_empty_train_id": empty_train[0] if empty_train else "",
            "train_pool_empty": len(empty_train),
            "jev_ranked_on_approved_rows": sum(1 for row in approvals if row["jev_applied"]),
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "fill_at_snapshot": {
            "pid": FILL_PID,
            "alive_at_record": pid_alive(FILL_PID),
            "args": "--limit 280 --max-minutes 80 --write-split",
            "do_not_start_another_while_alive": True,
            "weights_written": False,
        },
    }
    (SIDECAR_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "approvals": len(approvals),
        "first": approval_ids[0],
        "last": approval_ids[-1],
        "gaps": gaps,
        "skipped": skipped,
        "holdout_with_candidates": holdout_with_candidates,
        "notes_nonempty": notes_kept,
        "jev_applied": sum(1 for row in approvals if row["jev_applied"]),
        "snapshot_sha256": snapshot_sha,
        "workspace_changed_after_snapshot": after_sha != snapshot_sha,
        "live_jsonl_edited": False,
        "fill_pid_alive": pid_alive(FILL_PID),
        "with_gemini_candidates": with_candidates,
        "last_candidate_id": cand_ids[-1] if cand_ids else "",
        "sidecar": str(SIDECAR_DIR.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
