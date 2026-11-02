"""Build a 2,000-row spoken workspace and freeze the scale holdout.

Copies kp-001–kp-500 from spoken_500.jsonl, then appends original synthetic
English lines kp-501–kp-2000. Does not call Gemini, Jev, or a trainer.
Refuses to overwrite a scale file that already exists.

Licence stays unknown. New rows stay pending_native_review. No CC-BY is invented.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from claynext.models.benchmarks.spoken_split import plan_scale_holdout
from claynext.models.khmer_spoken.schema import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[4]
SPOKEN_500 = ROOT / "data/khmer_spoken/workspace/spoken_500.jsonl"
REMAINDER2 = ROOT / "data/khmer_spoken/versions/owner-approved-20261023-remainder-2/dialogue.jsonl"
WORKSPACE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
VERSION = ROOT / "data/khmer_spoken/versions/scale-lock1000-20261023"
FIXTURE = ROOT / "data/khmer_spoken/fixtures/dialogue_1500_scale.jsonl"

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the expansion past 500 rows toward "
    "10,000. Original English line, not a copy of kp-001 through kp-500 and "
    "not taken from a commercial video. Licence unknown. Not gold. "
    "Not owner-approved. Pending native review."
)
REVIEWER_NOTES = (
    "Synthetic English source only. No reference Khmer. "
    "review_status pending_native_review."
)

# category, relationship, speaker, listener, emotion, register, setting, text
# Each text is one original spoken line. 100 lines in each of 15 groups.
_GROUPS: list[tuple[str, str, str, str, str, list[str]]] = []


def _g(category: str, relationship: str, register: str, setting: str, people: str, lines: list[str]) -> None:
    if len(lines) != 100:
        raise SystemExit(f"{category} has {len(lines)} lines, expected 100")
    _GROUPS.append((category, relationship, register, setting, people, lines))


def _people(spec: str, index: int) -> tuple[str, str]:
    options = [pair.split(":") for pair in spec.split(",")]
    speaker, listener = options[index % len(options)]
    return speaker, listener


# People specs are speaker:listener pairs rotated per line.
_CHILD = "dara:mother,srey:father,nita:mother,rith:father,piseth:mother,lina:father,vanna:mother,sophea:father"
_PARENT = "mother:dara,father:srey,mother:nita,father:rith,mother:lina,father:piseth,mother:vanna,father:sophea"
_ROMANCE = "channary:vuthy,vuthy:channary,lina:sokha,sokha:lina,bopha:sopheak,sopheak:bopha"
_FRIENDS = "lina:srey,vuthy:rith,nita:bopha,srey:lina,rith:vuthy,bopha:nita"
_SIB = "dara:channary,channary:dara,srey:rith,rith:srey,nita:piseth,piseth:nita"
_WORK = "ms_sothea:sophea,sophea:ms_sothea,visal:piseth,piseth:visal"
_ELDER = "grandma_yeay:dara,grandpa_ta:lina,grandma_yeay:srey,grandpa_ta:nita,dara:grandma_yeay,lina:grandpa_ta"
_NEIGHBOR = "kosal:sopheak,sopheak:kosal,sokha:bopha,bopha:sokha"
_MARKET = "rachana:srey,srey:rachana,vendor_mao:vuthy,vuthy:vendor_mao"
_TRAVEL = "vuthy:lina,lina:vuthy,dara:mother,sopheak:bopha"
_SCHOOL = "ms_sothea:srey,srey:ms_sothea,visal:dara,dara:ms_sothea"
_CLINIC = "vuthy:doctor_nary,doctor_nary:vuthy,vanna:doctor_nary,doctor_nary:vanna"
_PAGODA = "bopha:venerable_sok,venerable_sok:bopha,nita:venerable_sok,piseth:venerable_sok"
_PHONE = "lina:mother,mother:lina,vuthy:sokha,sokha:vuthy,srey:father,father:srey"
_MIXED = "sopheak:visal,visal:sopheak,rith:vuthy,officer_meas:dara,dara:officer_meas,nita:stranger"


def _norm(text: str) -> str:
    cleaned = text.lower().replace("'", "'")
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _load_tagged() -> list[tuple[str, str, str, str, str, str]]:
    folder = Path(__file__).resolve().parent
    ns: dict = {}
    for name in ("scale_drafts_a.py", "scale_drafts_b.py", "scale_drafts_c.py"):
        exec((folder / name).read_text(encoding="utf-8"), ns)
    groups = list(ns["GROUPS_A"]) + list(ns["GROUPS_B"]) + list(ns["GROUPS_C"])
    meta = {row[0]: row for row in groups}
    tagged: list[tuple[str, str, str, str, str, str]] = []
    for category, relationship, register, setting, lines in groups:
        for line in lines:
            tag, text = line.split("|", 1)
            tagged.append((category, relationship, register, setting, tag.strip(), text.strip()))
    for category, lines in ns["EXTRAS"].items():
        relationship, register, setting = meta[category][1], meta[category][2], meta[category][3]
        for line in lines:
            tag, text = line.split("|", 1)
            tagged.append((category, relationship, register, setting, tag.strip(), text.strip()))
    return tagged


def _roles(category: str, tag: str, text: str, index: int) -> tuple[str, str, str]:
    """Return speaker, listener, relationship."""
    children = ("dara", "srey", "nita", "lina", "vanna", "piseth", "rith", "sophea")
    if text.startswith("Mom,") or text.startswith("Mom "):
        return children[index % len(children)], "mother", "child_to_parent"
    if text.startswith("Dad,") or text.startswith("Dad "):
        return children[index % len(children)], "father", "child_to_parent"
    if text.startswith("Sis,"):
        return "dara", "channary", "younger_to_older_sibling"
    if text.startswith("Teacher,"):
        return children[index % 5], "ms_sothea", "student_to_teacher"
    if text.startswith("Doctor,") or text.startswith("Nurse,"):
        return ("vuthy", "vanna", "srey", "lina")[index % 4], "doctor_nary", "patient_to_doctor"
    if text.startswith("Venerable,"):
        return ("bopha", "nita", "piseth", "sokha", "channary")[index % 5], "venerable_sok", "lay_to_monk"
    if text.startswith("Officer,"):
        return ("dara", "sokha", "bopha", "vuthy")[index % 4], "officer_meas", "police"
    if category == "parent_to_child":
        pairs = (
            ("mother", "dara"), ("father", "srey"), ("mother", "nita"), ("father", "rith"),
            ("mother", "lina"), ("father", "piseth"),
        )
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "parent_to_child"
    if category == "romantic":
        pairs = (
            ("channary", "vuthy"), ("vuthy", "channary"), ("lina", "sokha"),
            ("sokha", "lina"), ("bopha", "sopheak"), ("sopheak", "bopha"),
        )
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "romantic"
    if category == "friends_close":
        pairs = (("lina", "srey"), ("vuthy", "rith"), ("nita", "bopha"), ("srey", "lina"), ("rith", "vuthy"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "friends_close"
    if category == "siblings":
        pairs = (("channary", "dara"), ("rith", "srey"), ("piseth", "nita"), ("srey", "rith"))
        speaker, listener = pairs[index % len(pairs)]
        relation = "older_to_younger_sibling" if index % 2 == 0 else "younger_to_older_sibling"
        return speaker, listener, relation
    if category == "workplace":
        pairs = (("ms_sothea", "sophea"), ("sophea", "ms_sothea"), ("visal", "piseth"), ("piseth", "visal"))
        speaker, listener = pairs[index % len(pairs)]
        relation = "boss_to_employee" if index % 2 == 0 else "employee_to_boss"
        return speaker, listener, relation
    if category == "elder_home":
        pairs = (("grandma_yeay", "dara"), ("grandpa_ta", "lina"), ("grandma_yeay", "srey"), ("grandpa_ta", "nita"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "grandparent_to_grandchild"
    if category == "neighbors":
        pairs = (("kosal", "sopheak"), ("sopheak", "kosal"), ("sokha", "bopha"), ("bopha", "sokha"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "neighbor_to_neighbor"
    if category == "market":
        pairs = (("srey", "vendor_mao"), ("vuthy", "rachana"), ("lina", "vendor_mao"), ("rachana", "vuthy"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "customer_to_vendor"
    if category == "travel":
        pairs = (("vuthy", "lina"), ("lina", "vuthy"), ("dara", "mother"), ("sopheak", "bopha"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "travel"
    if category == "school":
        if tag == "formal":
            return "ms_sothea", children[index % 5], "teacher_to_student"
        return children[index % 5], "ms_sothea", "student_to_teacher"
    if category == "clinic":
        if tag == "formal":
            return "doctor_nary", ("vuthy", "vanna", "srey", "lina")[index % 4], "doctor_to_patient"
        return ("vuthy", "vanna", "srey", "lina")[index % 4], "doctor_nary", "patient_to_doctor"
    if category == "pagoda":
        return "venerable_sok", ("bopha", "lina", "nita", "piseth")[index % 4], "monk_to_lay"
    if category == "phone_call":
        pairs = (
            ("lina", "mother"), ("mother", "lina"), ("vuthy", "sokha"),
            ("srey", "father"), ("father", "srey"), ("sokha", "vuthy"),
        )
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "phone_call"
    if tag == "teasing":
        pairs = (("rith", "vuthy"), ("vuthy", "rith"), ("nita", "bopha"), ("srey", "lina"))
        speaker, listener = pairs[index % len(pairs)]
        return speaker, listener, "affectionate_teasing"
    pairs = (("nita", "stranger"), ("dara", "stranger"), ("sopheak", "visal"), ("visal", "sopheak"))
    speaker, listener = pairs[index % len(pairs)]
    return speaker, listener, "strangers"


def _draft_rows(existing_norms: set[str]) -> list[dict]:
    kept: list[tuple[str, str, str, str, str, str]] = []
    seen: set[str] = set()
    per_cat: dict[str, int] = {}
    for category, relationship, register, setting, tag, text in _load_tagged():
        key = _norm(text)
        if not key or key in existing_norms or key in seen:
            continue
        seen.add(key)
        kept.append((category, relationship, register, setting, tag, text))
        per_cat[category] = per_cat.get(category, 0) + 1
    if len(kept) < 1500:
        raise SystemExit(f"only {len(kept)} unique new lines after dropping copies")
    while len(kept) > 1500:
        biggest = max(per_cat, key=lambda name: per_cat[name])
        for index in range(len(kept) - 1, -1, -1):
            if kept[index][0] == biggest:
                del kept[index]
                per_cat[biggest] -= 1
                break
    rows = []
    cat_index: dict[str, int] = {}
    for category, _relationship, register, setting, tag, text in kept:
        index = cat_index.get(category, 0)
        cat_index[category] = index + 1
        speaker, listener, relationship = _roles(category, tag, text, index)
        if tag == "formal":
            emotion, line_register = "neutral", "formal"
        elif tag == "teasing":
            emotion, line_register = "teasing", "casual"
        else:
            emotion, line_register = tag, register
        if tag not in {"formal", "teasing", "worried", "neutral", "happy", "sad", "tired", "afraid", "tender", "angry"}:
            raise SystemExit(f"unknown emotion tag {tag} on {text}")
        words = text.split()
        if not 6 <= len(words) <= 22:
            raise SystemExit(f"line length {len(words)}: {text}")
        rows.append({
            "source_text": text,
            "speaker_id": speaker,
            "listener_id": listener,
            "relationship": relationship,
            "emotion": emotion,
            "register": line_register or "neutral",
            "category": category,
            "setting": setting,
        })
    if len(rows) != 1500:
        raise SystemExit(f"expected 1500 drafts, got {len(rows)}")
    if len({row["source_text"] for row in rows}) != 1500:
        raise SystemExit("draft source lines are not unique")
    return rows


def _row_dict(number: int, draft: dict, *, locked: bool) -> dict:
    return {
        "id": f"kp-{number:03d}",
        "source_text": draft["source_text"],
        "source_lang": "en",
        "target_lang": "km",
        "stub_khmer": "",
        "candidates": [],
        "approved_text": "",
        "speaker_id": draft["speaker_id"],
        "listener_id": draft["listener_id"],
        "relationship": draft["relationship"],
        "emotion": draft["emotion"],
        "register": draft["register"],
        "category": draft["category"],
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
            "source_file": "data/khmer_spoken/fixtures/dialogue_1500_scale.jsonl",
            "licence": None,
            "not_for_gold": True,
            "not_for_weight_training": True,
            "locked_from_training": locked,
            "scale_pool": "locked" if locked else "train",
            "setting": draft["setting"],
            "expansion": "kp-501-kp-2000",
            "created_on": "2026-10-23",
            "note": "Synthetic draft. No external licence was invented. Not a weight update.",
        },
        "schema_version": SCHEMA_VERSION,
    }


def _mark_existing_scale(row: dict, *, train_ids: set[str]) -> None:
    if row["id"] in train_ids:
        meta = row.setdefault("metadata", {})
        if meta.get("locked_from_training"):
            meta["prior_plan_locked"] = True
            meta["prior_plan"] = "train100-locked400-20261023"
        meta["locked_from_training"] = False
        meta["scale_pool"] = "train"
        meta["scale_version"] = "scale-lock1000-20261023"
        return
    meta = row.setdefault("metadata", {})
    meta["locked_from_training"] = True
    meta["scale_pool"] = "locked"
    meta["scale_version"] = "scale-lock1000-20261023"


def _write_version(plan: dict, source_sha: str, rows_with_candidates: int, jev_ranked: int) -> None:
    VERSION.mkdir(parents=True, exist_ok=True)
    (VERSION / "train_ids.txt").write_text("\n".join(plan["train_ids"]) + "\n", encoding="utf-8")
    (VERSION / "locked_ids.txt").write_text("\n".join(plan["locked_ids"]) + "\n", encoding="utf-8")
    manifest = {
        "version": plan["version"],
        "schema": plan["schema"],
        "created_on": "2026-10-23",
        "dry_run": True,
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "promotion": "not_promoted",
        "hosted_fine_tune": "not_started",
        "vertex_fine_tune": "not_called",
        "licence": "unknown",
        "invented_external_licence": False,
        "owner_request": (
            "Dataset 10,000–30,000. Benchmark holdout 1,000–2,000. "
            "Model sizes 3B, 7B/8B, and 14B were named. This cut does not train them."
        ),
        "teacher": "gemini",
        "ranker": "jev",
        "gemini_and_jev_are_not_a_weight_update": True,
        "blocked_model_sizes": ["3B", "7B", "8B", "14B"],
        "blocked_reason": "16 GB M4. trainer.start still refuses 3B, 7B, 8B, and 14B.",
        "scores": {"chrf": "not_measured", "comet": "not_measured", "human": "not_measured"},
        "native_gold_benchmark": False,
        "not_the_1000_to_2000_native_gold_benchmark": True,
        "dataset_rows_target": plan["dataset_rows_target"],
        "native_benchmark_rows_target": plan["native_benchmark_rows_target"],
        "note": plan["note"],
        "rule": plan["rule"],
        "cut_frozen": True,
        "sliding_the_window_later_is_forbidden": True,
        "prior_directories_deleted": False,
        "prior_plans_kept": [
            "data/khmer_spoken/versions/heldout-locked-20261023-kp081-100",
            "data/khmer_spoken/versions/train100-locked400-20261023",
            "data/khmer_spoken/versions/spoken-500-train100-spec-20261023",
        ],
        "split": {
            "rule": "last 1000 ids locked; earlier ids are the train pool",
            "train_count": plan["train_count"],
            "locked_count": plan["locked_count"],
            "train_id_first": plan["train_id_first"],
            "train_id_last": plan["train_id_last"],
            "locked_id_first": plan["locked_id_first"],
            "locked_id_last": plan["locked_id_last"],
            "train_on_locked": False,
            "tune_on_locked": False,
            "locked_use": "benchmark pool only; never training and never hyperparameter tuning",
            "train_pool_meaning": (
                "Ids reserved for a later adapter. Licence is unknown. "
                "kp-101 onward stay pending_native_review. This pool is not a clearance to train."
            ),
        },
        "historical_flag_note": (
            "kp-101–kp-500 were locked_from_training in the 500-row plan. "
            "In this scale copy that flag is cleared and prior_plan_locked is set, "
            "because those ids are now in the train pool. spoken_500.jsonl was not edited. "
            "The old version directory was not edited."
        ),
        "workspace": "data/khmer_spoken/workspace/spoken_scale.jsonl",
        "prior_workspace_unchanged": "data/khmer_spoken/workspace/spoken_500.jsonl",
        "source_text_sha256": source_sha,
        "rows_total": plan["row_count"],
        "rows_with_candidates_at_cut": rows_with_candidates,
        "jev_ranked_at_cut": jev_ranked,
        "resume": (
            "PYTHONPATH=src .venv/bin/python "
            "data/outputs/voice_training/2026-10-23-spoken-500/fill_scale.py --limit 25 --write-split"
        ),
    }
    (VERSION / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line if line.endswith("\n") else line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    if WORKSPACE.exists():
        raise SystemExit(f"refusing to overwrite {WORKSPACE}")
    raw_500 = [line for line in SPOKEN_500.read_text(encoding="utf-8").splitlines() if line.strip()]
    head = [line for line in REMAINDER2.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(raw_500) != 500 or raw_500[:100] != head:
        raise SystemExit("spoken_500 head does not match remainder-2")
    existing = [json.loads(line) for line in raw_500]
    existing_norms = {_norm(row["source_text"]) for row in existing}
    drafts = _draft_rows(existing_norms)
    new_rows_stub = [{"id": f"kp-{index:03d}"} for index in range(1, 2001)]
    plan = plan_scale_holdout([row["id"] for row in new_rows_stub])
    if plan["train_id_last"] != "kp-1000" or plan["locked_id_first"] != "kp-1001":
        raise SystemExit("scale cut is not kp-001–kp-1000 train and kp-1001–kp-2000 locked")
    train_ids = set(plan["train_ids"])
    locked_ids = set(plan["locked_ids"])
    for row in existing[100:]:
        _mark_existing_scale(row, train_ids=train_ids)
        if row.get("review_status") != "pending_native_review" or row.get("license_type") != "unknown":
            raise SystemExit(f"{row['id']} review or licence changed")
    built = []
    for offset, draft in enumerate(drafts, start=501):
        row_id = f"kp-{offset:03d}"
        built.append(_row_dict(offset, draft, locked=row_id in locked_ids))
    lines = list(raw_500[:100])
    lines.extend(json.dumps(row, ensure_ascii=False) for row in existing[100:])
    lines.extend(json.dumps(row, ensure_ascii=False) for row in built)
    _write_lines(WORKSPACE, lines)
    _write_lines(FIXTURE, [json.dumps(row, ensure_ascii=False) for row in built])
    disk = [json.loads(line) for line in WORKSPACE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row["id"] for row in disk] != [f"kp-{index:03d}" for index in range(1, 2001)]:
        raise SystemExit("workspace ids are not kp-001 through kp-2000")
    if [json.loads(line)["source_text"] for line in raw_500] != [row["source_text"] for row in disk[:500]]:
        raise SystemExit("first 500 source texts changed")
    source_sha = hashlib.sha256("\n".join(row["source_text"] for row in disk).encode("utf-8")).hexdigest()
    jev_ranked = sum(1 for row in disk if (row.get("metadata") or {}).get("jev", {}).get("applied"))
    with_cands = sum(
        1 for row in disk if any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or []))
    )
    _write_version(plan, source_sha, with_cands, jev_ranked)
    print(
        f"SOURCES rows={len(disk)} new={len(built)} with_candidates={with_cands} "
        f"jev_ranked={jev_ranked} train={plan['train_id_first']}..{plan['train_id_last']} "
        f"locked={plan['locked_id_first']}..{plan['locked_id_last']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
