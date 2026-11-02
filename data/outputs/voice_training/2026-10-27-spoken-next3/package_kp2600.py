"""Package stored Jev lines from spoken_train_next3.jsonl into a new train export.

Reads spoken_scale.jsonl, spoken_train_next.jsonl, spoken_train_next2.jsonl,
and spoken_train_next3.jsonl. Does not write the first three. May store a Jev
line on a next3 row that already has candidate text and no stored Jev line.
Does not change live review fields. Does not call trainer.start.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.jev_decisions import rank_khmer_candidates
from claynext.models.khmer_spoken.schema import DialogueExample

ROOT = Path(__file__).resolve().parents[4]
SCALE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
NEXT = ROOT / "data/khmer_spoken/workspace/spoken_train_next.jsonl"
NEXT2 = ROOT / "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
NEXT3 = ROOT / "data/khmer_spoken/workspace/spoken_train_next3.jsonl"
LOCK = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
OPEN_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl"
PRIOR_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-b/sft-train-approved.jsonl"
C_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261026-c/sft-train-approved.jsonl"
D_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261027-d/sft-train-approved.jsonl"
E_SFT = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261027-e/sft-train-approved.jsonl"
PRIOR_GRANT = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2400"
SIDECAR_DIR = ROOT / "data/khmer_spoken/versions/owner-approval-sidecar-20261027-kp2600"
GRANT_DIR = ROOT / "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2600"
SFT_DIR = ROOT / "data/khmer_spoken/versions/translate-sft-spoken-20261027-f"
OWNER_QUOTE = "if licence is still unknown i approve you do sometihnk and continue trained."
SESSION_QUOTE = "finish the jobs for licence unknown and null translations by ranking them"
SCALE_SHA_EXPECTED = "c9a14bfaacf91261c6f3b88502afd3761c7dd6ad0b3131fcb03ed9dc54ddb662"
NEXT_SHA_EXPECTED = "9543a34ae84356013624e34a033964f87ee7f7e3a945ce1204c04ed6610350ea"
NEXT2_SHA_EXPECTED = "394f1e26687bd153e2c9e987c1774ae3863227ed026954a2ad9aa200d9551dd9"
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
    "origin",
    "candidates",
)
KEY_MARKERS = ("AIza", "sk-", "hf_", "ghp_", "xoxb-", "api_key", "BEGIN PRIVATE")
FILL_SCRIPTS = {"fill_next3.py", "fill_next2.py", "fill_scale.py", "fill_next.py"}


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


def holdout_number(row_id: str) -> bool:
    number = kp_num(row_id)
    return 1001 <= number <= 2000


def read_stable(path: Path) -> tuple[bytes, list[dict]]:
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise SystemExit(f"{path.name} changed between two reads; nothing written")
    rows = [json.loads(line) for line in first.decode("utf-8").splitlines() if line.strip()]
    return first, rows


def fill_alive() -> str:
    proc = subprocess.run(["ps", "-ax", "-o", "pid=,comm=,args="], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("could not list processes; nothing written")
    hits: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid_text, comm, args = parts
        if not pid_text.isdigit():
            continue
        if not Path(comm).name.lower().startswith("python"):
            continue
        names = {Path(token).name for token in args.split()}
        if names & FILL_SCRIPTS or any(name.startswith("fill_kp") for name in names):
            hits.append(f"{pid_text} {args.strip()}")
    return hits[0] if hits else ""


def remove_new_dirs() -> None:
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            shutil.rmtree(path)


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line if line.endswith("\n") else line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def frozen_view(row: dict) -> tuple:
    return tuple(json.dumps(row.get(key), ensure_ascii=False, sort_keys=True) for key in FROZEN)


def rank_missing(rows: list[dict]) -> int:
    """Call rank_khmer_candidates once per row that has text and no stored Jev line."""
    applied = 0
    for index, row in enumerate(rows):
        if not has_candidate(row) or jev_text(row):
            continue
        before = json.loads(json.dumps(row))
        frozen = frozen_view(before)
        try:
            example = DialogueExample.from_dict(json.loads(json.dumps(before)))
            result = rank_khmer_candidates(example)
        except Exception:
            rows[index] = before
            continue
        if not result.get("applied"):
            rows[index] = before
            continue
        updated = json.loads(json.dumps(before))
        meta = dict(updated.get("metadata") or {})
        meta["jev"] = dict(example.metadata.get("jev") or result)
        updated["metadata"] = meta
        if frozen_view(updated) != frozen or not jev_text(updated):
            rows[index] = before
            continue
        if updated.get("review_status") != "pending_native_review":
            rows[index] = before
            continue
        if updated.get("license_type") != "unknown":
            rows[index] = before
            continue
        if updated.get("verified_by") or str(updated.get("approved_text") or "").strip():
            rows[index] = before
            continue
        rows[index] = updated
        applied += 1
    return applied


def sft_row(row_id: str, source: str, khmer: str) -> dict:
    return {
        "id": row_id,
        "source": source,
        "khmer": khmer,
        "licence": "unknown",
        "owner_training_approved": True,
        "split": "train",
    }


def grant_row(row_id: str, source_file: str) -> dict:
    return {
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
        "source_file": source_file,
    }


def source_file_for(row_id: str) -> str:
    number = kp_num(row_id)
    if number <= 1000:
        return "data/khmer_spoken/workspace/spoken_scale.jsonl"
    if 2001 <= number <= 2200:
        return "data/khmer_spoken/workspace/spoken_train_next.jsonl"
    if 2201 <= number <= 2400:
        return "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
    if 2401 <= number <= 2600:
        return "data/khmer_spoken/workspace/spoken_train_next3.jsonl"
    raise SystemExit(f"{row_id} is outside the train ranges")


def main() -> None:
    running = fill_alive()
    if running:
        raise SystemExit(f"a fill process is running; nothing written: {running}")
    for path in (SIDECAR_DIR, GRANT_DIR, SFT_DIR):
        if path.exists():
            raise SystemExit(f"refusing to overwrite {path}")
    protected = (
        OPEN_SFT,
        PRIOR_SFT,
        C_SFT,
        D_SFT,
        E_SFT,
        SCALE,
        NEXT,
        NEXT2,
        NEXT3,
        PRIOR_GRANT / "grants.jsonl",
    )
    for path in protected:
        if not path.is_file():
            raise SystemExit(f"missing {path}; nothing written")

    open_sft_sha = sha256_file(OPEN_SFT)
    prior_sft_sha = sha256_file(PRIOR_SFT)
    c_sft_sha = sha256_file(C_SFT)
    d_sft_sha = sha256_file(D_SFT)
    e_sft_sha = sha256_file(E_SFT)
    counts = (
        line_count(OPEN_SFT),
        line_count(PRIOR_SFT),
        line_count(C_SFT),
        line_count(D_SFT),
        line_count(E_SFT),
    )
    if counts != (720, 758, 1000, 1200, 1400):
        raise SystemExit(f"prior SFT line counts are {counts}; nothing written")

    locked_ids = load_ids(LOCK / "locked_ids.txt")
    expected_locked = [f"kp-{index:03d}" for index in range(1001, 2001)]
    if locked_ids != expected_locked:
        raise SystemExit("scale lock is not holdout kp-1001–kp-2000")
    locked_bytes = (LOCK / "locked_ids.txt").read_bytes()
    locked_sha = sha256_bytes(locked_bytes)

    scale_raw, scale_rows = read_stable(SCALE)
    next_raw, next_rows = read_stable(NEXT)
    next2_raw, next2_rows = read_stable(NEXT2)
    next3_raw, next3_rows = read_stable(NEXT3)
    scale_sha = sha256_bytes(scale_raw)
    next_sha = sha256_bytes(next_raw)
    next2_sha = sha256_bytes(next2_raw)
    next3_sha_before = sha256_bytes(next3_raw)
    if scale_sha != SCALE_SHA_EXPECTED:
        raise SystemExit("spoken_scale.jsonl sha256 changed; nothing written")
    if next_sha != NEXT_SHA_EXPECTED:
        raise SystemExit("spoken_train_next.jsonl sha256 changed; nothing written")
    if next2_sha != NEXT2_SHA_EXPECTED:
        raise SystemExit("spoken_train_next2.jsonl sha256 changed; nothing written")

    expected_scale = [f"kp-{index:03d}" for index in range(1, 2001)]
    expected_train = expected_scale[:1000]
    expected_next = [f"kp-{index:04d}" for index in range(2001, 2201)]
    expected_next2 = [f"kp-{index}" for index in range(2201, 2401)]
    expected_next3 = [f"kp-{index}" for index in range(2401, 2601)]
    expected_prior = expected_train + expected_next + expected_next2
    if [row.get("id") for row in scale_rows] != expected_scale:
        raise SystemExit("spoken_scale ids are not kp-001–kp-2000; nothing written")
    if [row.get("id") for row in next_rows] != expected_next:
        raise SystemExit("spoken_train_next ids are not kp-2001–kp-2200; nothing written")
    if [row.get("id") for row in next2_rows] != expected_next2:
        raise SystemExit("spoken_train_next2 ids are not kp-2201–kp-2400; nothing written")
    if [row.get("id") for row in next3_rows] != expected_next3:
        raise SystemExit("spoken_train_next3 ids are not kp-2401–kp-2600; nothing written")
    if len(next3_rows) != 200:
        raise SystemExit("spoken_train_next3 is not 200 rows; nothing written")

    scale_by_id = {row["id"]: row for row in scale_rows}
    next_by_id = {row["id"]: row for row in next_rows}
    next2_by_id = {row["id"]: row for row in next2_rows}
    holdout_filled = [
        row["id"]
        for row in scale_rows
        if holdout_number(row["id"]) and (has_candidate(row) or jev_text(row))
    ]
    if holdout_filled:
        raise SystemExit(f"holdout_filled {len(holdout_filled)}; nothing written")

    e_rows = [json.loads(line) for line in E_SFT.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row.get("id") for row in e_rows] != expected_prior:
        raise SystemExit("the -e export is not the 1,400 train rows; nothing written")
    if line_count(PRIOR_GRANT / "grants.jsonl") != 1400:
        raise SystemExit("the kp2400 grant is not 1,400 rows; nothing written")

    needs_rank = [row["id"] for row in next3_rows if has_candidate(row) and not jev_text(row)]
    ranked_now = rank_missing(next3_rows) if needs_rank else 0
    if ranked_now:
        write_lines(NEXT3, [json.dumps(row, ensure_ascii=False) for row in next3_rows])
        next3_raw, next3_rows = read_stable(NEXT3)
    next3_sha_after = sha256_bytes(next3_raw)
    if ranked_now == 0 and next3_sha_after != next3_sha_before:
        raise SystemExit("spoken_train_next3.jsonl changed without a Jev write")

    if SCALE.read_bytes() != scale_raw or NEXT.read_bytes() != next_raw or NEXT2.read_bytes() != next2_raw:
        raise SystemExit("a live file other than next3 changed; export not written")
    if fill_alive():
        raise SystemExit("a fill process appeared; export not written")

    def live_for(row_id: str) -> dict:
        number = kp_num(row_id)
        if number <= 1000:
            return scale_by_id[row_id]
        if number <= 2200:
            return next_by_id[row_id]
        if number <= 2400:
            return next2_by_id[row_id]
        raise SystemExit(f"{row_id} is not in the prior train files")

    def live_jev(row: dict, row_id: str) -> tuple[str, str]:
        example = DialogueExample.from_dict(row)
        ranked = jev_text(row)
        if example.training_khmer().strip() != ranked or not ranked or not has_khmer(ranked):
            raise SystemExit(f"{row_id} has no stored Jev line")
        source = example.source_text.strip()
        if not source or source == ranked or has_khmer(source):
            raise SystemExit(f"{row_id} source check failed")
        if example.license_type != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown")
        return source, ranked

    sft_rows: list[dict] = []
    grants: list[dict] = []
    for e_row, row_id in zip(e_rows, expected_prior, strict=True):
        source, ranked = live_jev(live_for(row_id), row_id)
        if e_row.get("source") != source or e_row.get("khmer") != ranked:
            raise SystemExit(f"{row_id} -e line is not the stored Jev line; nothing written")
        if e_row.get("licence") != "unknown" or e_row.get("owner_training_approved") is not True:
            raise SystemExit(f"{row_id} -e approval fields are unexpected; nothing written")
        if e_row.get("split") != "train":
            raise SystemExit(f"{row_id} -e split is not train; nothing written")
        sft_rows.append(sft_row(row_id, source, ranked))
        grants.append(grant_row(row_id, source_file_for(row_id)))

    approvals: list[dict] = []
    empty_ids: list[str] = []
    filled_ids: list[str] = []
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for row in next3_rows:
        row_id = row["id"]
        if holdout_number(row_id) or not (2401 <= kp_num(row_id) <= 2600):
            raise SystemExit(f"{row_id} is outside kp-2401–kp-2600; nothing written")
        if str(row.get("review_status") or "") != "pending_native_review":
            raise SystemExit(f"{row_id} is not pending_native_review; nothing written")
        if str(row.get("license_type") or "") != "unknown":
            raise SystemExit(f"{row_id} licence is not unknown; nothing written")
        if row.get("verified_by") or str(row.get("approved_text") or "").strip():
            raise SystemExit(f"{row_id} already has a live approval; nothing written")
        if (row.get("metadata") or {}).get("human") is True:
            raise SystemExit(f"{row_id} is marked human; nothing written")
        ranked = jev_text(row)
        if not ranked:
            empty_ids.append(row_id)
            continue
        if row.get("origin") != "gemini_teacher":
            raise SystemExit(f"{row_id} origin is not gemini_teacher; nothing written")
        source, ranked = live_jev(row, row_id)
        filled_ids.append(row_id)
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
            "candidate_count": candidate_count(row),
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
            "source_file": "data/khmer_spoken/workspace/spoken_train_next3.jsonl",
        })
        sft_rows.append(sft_row(row_id, source, ranked))
        grants.append(grant_row(row_id, "data/khmer_spoken/workspace/spoken_train_next3.jsonl"))

    if not filled_ids:
        print(json.dumps({
            "export_written": False,
            "reason": "no new Jev line beyond the 1,400-row -e export",
            "next3_filled": 0,
            "next3_empty": len(empty_ids),
            "ranked_this_pass": ranked_now,
            "holdout_filled": 0,
            "started": False,
            "weights_written": False,
            "trainer_start_called": False,
        }, indent=2))
        return

    last_filled = filled_ids[-1]
    expected_through = [f"kp-{index}" for index in range(2401, kp_num(last_filled) + 1)]
    gaps = [row_id for row_id in expected_through if row_id not in filled_ids]
    if any(holdout_number(row["id"]) for row in sft_rows):
        raise SystemExit("holdout id in the export; nothing written")
    if [row["id"] for row in sft_rows] != expected_prior + filled_ids:
        raise SystemExit("export ids are not the stored train Jev lines; nothing written")
    if len(sft_rows) != 1400 + len(filled_ids) or len(grants) != len(sft_rows):
        raise SystemExit("grant and sft counts diverged; nothing written")
    if len(approvals) != len(filled_ids):
        raise SystemExit("sidecar count is not the newly filled count; nothing written")
    if any(row.get("started") for row in sft_rows):
        raise SystemExit("a train row was marked started")

    last_num = kp_num(last_filled)
    empty_note = ""
    if gaps:
        empty_note = f" Still-empty ids inside that span are excluded ({len(gaps)})."
    grant_statement = (
        "The project owner approved training use of the listed spoken Khmer rows "
        "while license_type remains unknown. This grant covers kp-001–kp-1000 and "
        f"kp-2001–{last_filled} only.{empty_note} It is not CC-BY and not any other "
        "external licence. Holdout rows kp-1001–kp-2000 are not included and were not changed."
    )
    model_card = f"""# Spoken Khmer train export

{len(sft_rows)} stored Jev lines. This file is not a trained language model. It is not promoted. The licence is unknown. No weights were written.

| Field | Value |
| --- | --- |
| File | `sft-train-approved.jsonl` |
| Rows | {len(sft_rows)} |
| Ids | kp-001–kp-1000, kp-2001–{last_filled} |
| Split | train |
| Khmer line | stored Jev line |
| Licence | unknown |
| owner_training_approved | true |
| Owner grant | `data/khmer_spoken/versions/owner-licence-grant-20261027-kp2600/` |
| External licence | none recorded. This grant is not CC-BY. |
| Promotion | not_promoted |
| Holdout | excluded. Holdout count in this file is 0. |
| Weights | none written, none uploaded |
| started | false |

`trainer.start` was not called. Live review fields were not changed. Holdout kp-1001–kp-2000 is excluded. Still-empty ids were excluded.
"""
    sidecar_manifest = {
        "version": "owner-approval-sidecar-20261027-kp2600",
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
            f"remains unknown. This sidecar records that approval for training-export use "
            f"on {filled_ids[0]}–{last_filled} only. It is not CC-BY, not a native-reviewer "
            "gold mark, and not a fine-tune launch."
        ),
        "why_sidecar": (
            "The newly filled rows live in spoken_train_next3.jsonl and stay "
            "pending_native_review there. Earlier approvals stay in the prior sidecars. "
            "Holdout kp-1001–kp-2000 is not approved."
        ),
        "live_jsonl_edited": ranked_now > 0,
        "live_review_fields_edited": False,
        "live_files_not_rewritten": [
            "data/khmer_spoken/workspace/spoken_scale.jsonl",
            "data/khmer_spoken/workspace/spoken_train_next.jsonl",
            "data/khmer_spoken/workspace/spoken_train_next2.jsonl",
        ] + ([] if ranked_now else ["data/khmer_spoken/workspace/spoken_train_next3.jsonl"]),
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "snapshot_sha256_train_next2": next2_sha,
        "snapshot_sha256_train_next3_before_rank": next3_sha_before,
        "snapshot_sha256_train_next3": next3_sha_after,
        "ranked_this_pass": ranked_now,
        "prior_version_kept": "data/khmer_spoken/versions/owner-approval-sidecar-20261027-kp2400",
        "locked_ids_unchanged": True,
        "locked_ids_sha256": locked_sha,
        "locked_ids_match_scale_lock": True,
        "split": {
            "rule": "holdout kp-1001–kp-2000 stays locked; this sidecar is the newly filled next3 ids",
            "new_approvals_first": filled_ids[0],
            "new_approvals_last": last_filled,
            "new_approvals_count": len(filled_ids),
            "new_approval_gaps": gaps,
            "holdout_approved": 0,
            "holdout_with_candidates": 0,
            "train_on_locked": False,
            "tune_on_locked": False,
        },
        "approval": {
            "recorded_in": "approvals.jsonl",
            "applied_to_live_jsonl": False,
            "purpose": "training-export",
            "count": len(filled_ids),
            "first_id": filled_ids[0],
            "last_id": last_filled,
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
            "train_next3_rows": 200,
            "train_next3_filled": len(filled_ids),
            "train_next3_empty": len(empty_ids),
            "jev_ranked": len(filled_ids),
            "holdout_filled": 0,
        },
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    grant_manifest = {
        "version": "owner-licence-grant-20261027-kp2600",
        "schema": "spoken-owner-licence-grant-1",
        "created_at": created,
        "statement": grant_statement,
        "owner_quote": OWNER_QUOTE,
        "session_quote": SESSION_QUOTE,
        "owner_quote_scope": (
            "Standing project-owner approval that training use is allowed while licence "
            f"remains unknown. This grant covers kp-001–kp-1000 and kp-2001–{last_filled} "
            "only. It is not an external licence. It does not change holdout rows, invent "
            "CC-BY, mark native gold, promote, call Vertex, or launch a 3B, 7B, 8B, or 14B fine-tune."
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
        "live_review_fields_edited": False,
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
        "id_ranges": ["kp-001–kp-1000", f"kp-2001–{last_filled}"],
        "included_count": len(grants),
        "included_ids_file": "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2600/train_ids.txt",
        "excluded_holdout": "kp-1001–kp-2000",
        "excluded_empty_ids": empty_ids,
        "prior_grant_kept": "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2400",
        "prior_grant_overwritten": False,
        "prior_grant_included_count": 1400,
        "gaps_are_holdout_only": not gaps,
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "snapshot_sha256_train_next2": next2_sha,
        "snapshot_sha256_train_next3": next3_sha_after,
        "last_filled_new_id": last_filled,
        "last_filled_number": last_num,
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "jobs_left_blocked": ["JOB-011", "JOB-019", "JOB-020", "JOB-021", "JOB-022"],
        "job_026": "IN_PROGRESS",
        "ten_thousand_row_target_met": False,
    }
    sft_manifest = {
        "version": "translate-sft-spoken-20261027-f",
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
        "licence_grant": "data/khmer_spoken/versions/owner-licence-grant-20261027-kp2600",
        "licence_grant_statement": grant_statement,
        "approval_sidecar": "data/khmer_spoken/versions/owner-approval-sidecar-20261027-kp2600",
        "target_rule": (
            "Every train row with a stored Jev line: kp-001–kp-1000, kp-2001–kp-2400, "
            f"and filled ids {filled_ids[0]}–{last_filled}. Still-empty ids are excluded. "
            "Holdout ids are excluded. The khmer field is the stored Jev line."
        ),
        "prior_open_sft_left_unmodified": True,
        "prior_open_sft_lines_before": 720,
        "prior_open_sft_sha256_before": open_sft_sha,
        "prior_b_sft_left_unmodified": True,
        "prior_b_sft_lines_before": 758,
        "prior_b_sft_sha256_before": prior_sft_sha,
        "prior_c_sft_left_unmodified": True,
        "prior_c_sft_lines_before": 1000,
        "prior_c_sft_sha256_before": c_sft_sha,
        "prior_d_sft_left_unmodified": True,
        "prior_d_sft_lines_before": 1200,
        "prior_d_sft_sha256_before": d_sft_sha,
        "prior_e_sft_left_unmodified": True,
        "prior_e_sft_lines_before": 1400,
        "prior_e_sft_sha256_before": e_sft_sha,
        "path": "data/khmer_spoken/versions/translate-sft-spoken-20261027-f/sft-train-approved.jsonl",
        "row_count": len(sft_rows),
        "from_prior_train": 1400,
        "from_train_next3_jev": len(filled_ids),
        "id_ranges": ["kp-001–kp-1000", f"kp-2001–{last_filled}"],
        "id_first": "kp-001",
        "id_last": last_filled,
        "split": "train",
        "fields": ["id", "source", "khmer", "licence", "owner_training_approved", "split"],
        "from_jev_count": len(sft_rows),
        "stub_used_count": 0,
        "holdout_excluded": True,
        "holdout_ids_in_export": 0,
        "holdout_filled": 0,
        "started_flag": False,
        "live_review_fields_edited": False,
        "snapshot_sha256_scale": scale_sha,
        "snapshot_sha256_train_next": next_sha,
        "snapshot_sha256_train_next2": next2_sha,
        "snapshot_sha256_train_next3": next3_sha_after,
        "excluded_empty_ids": empty_ids,
        "model_card": "data/khmer_spoken/versions/translate-sft-spoken-20261027-f/model-card.md",
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
            "".join(f"{row_id}\n" for row_id in filled_ids),
            encoding="utf-8",
        )
        (SIDECAR_DIR / "locked_ids.txt").write_bytes(locked_bytes)
        (GRANT_DIR / "grants.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in grants),
            encoding="utf-8",
        )
        (GRANT_DIR / "train_ids.txt").write_text(
            "".join(f"{row['id']}\n" for row in grants),
            encoding="utf-8",
        )
        sft_text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in sft_rows)
        (SFT_DIR / "sft-train-approved.jsonl").write_text(sft_text, encoding="utf-8")
        (SFT_DIR / "exported_ids.txt").write_text(
            "".join(f"{row['id']}\n" for row in sft_rows),
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

        if SCALE.read_bytes() != scale_raw or NEXT.read_bytes() != next_raw or NEXT2.read_bytes() != next2_raw:
            raise SystemExit("a protected live jsonl changed during the write")
        if ranked_now == 0 and NEXT3.read_bytes() != next3_raw:
            raise SystemExit("spoken_train_next3.jsonl changed during the write")
        if sha256_file(OPEN_SFT) != open_sft_sha or line_count(OPEN_SFT) != 720:
            raise SystemExit("open sft.jsonl changed")
        if sha256_file(PRIOR_SFT) != prior_sft_sha or line_count(PRIOR_SFT) != 758:
            raise SystemExit("758-row SFT file changed")
        if sha256_file(C_SFT) != c_sft_sha or line_count(C_SFT) != 1000:
            raise SystemExit("1000-row -c SFT file changed")
        if sha256_file(D_SFT) != d_sft_sha or line_count(D_SFT) != 1200:
            raise SystemExit("1200-row -d SFT file changed")
        if sha256_file(E_SFT) != e_sft_sha or line_count(E_SFT) != 1400:
            raise SystemExit("1400-row -e SFT file changed")
        if sha256_file(SIDECAR_DIR / "locked_ids.txt") != locked_sha:
            raise SystemExit("copied locked ids do not match the scale lock")
        written_sft = [
            json.loads(line)
            for line in (SFT_DIR / "sft-train-approved.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        holdout_in_export = sum(1 for row in written_sft if holdout_number(row["id"]))
        if holdout_in_export:
            raise SystemExit("holdout id was written into the export")
        if any(row.get("licence") != "unknown" or row.get("split") != "train" for row in written_sft):
            raise SystemExit("export licence or split drifted")
        if any(row.get("owner_training_approved") is not True for row in written_sft):
            raise SystemExit("export approval flag drifted")
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
        "export_written": True,
        "export_path": "data/khmer_spoken/versions/translate-sft-spoken-20261027-f/sft-train-approved.jsonl",
        "sft_count": len(sft_rows),
        "last_filled_id": last_filled,
        "next3_filled": len(filled_ids),
        "next3_empty": len(empty_ids),
        "next3_total": 200,
        "sidecar_count": len(approvals),
        "sidecar_first": filled_ids[0],
        "sidecar_last": last_filled,
        "grant_count": len(grants),
        "holdout_ids_in_export": 0,
        "holdout_filled": 0,
        "ranked_this_pass": ranked_now,
        "needs_rank_before": len(needs_rank),
        "started": False,
        "weights_written": False,
        "trainer_start_called": False,
        "fill_started": False,
        "live_review_fields_edited": False,
        "scale_sha256_unchanged": scale_sha,
        "train_next_sha256_unchanged": next_sha,
        "train_next2_sha256_unchanged": next2_sha,
        "train_next3_sha256": next3_sha_after,
        "open_sft_sha256_unchanged": open_sft_sha,
        "prior_b_sha256_unchanged": prior_sft_sha,
        "prior_c_sha256_unchanged": c_sft_sha,
        "prior_d_sha256_unchanged": d_sft_sha,
        "prior_e_sha256_unchanged": e_sft_sha,
        "sft_sha256": sft_manifest["sft_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
