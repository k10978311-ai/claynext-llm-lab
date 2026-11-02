"""Write kp-2601–kp-2800 source rows into a new train-pool file.

Reads spoken_scale.jsonl, spoken_train_next.jsonl, spoken_train_next2.jsonl,
and spoken_train_next3.jsonl only to reject duplicate source text. Does not
write those files, does not fill candidates, and does not start a trainer.

The refusal is the same gate as write_train_next.py: exact normalized copies,
content-word overlap at or above 0.42, and shared content 5-grams. This pass
applies that gate to kp-001–kp-2600 and inside the new file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path

from claynext.models.khmer_spoken.schema import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[4]
SCALE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
PRIOR = ROOT / "data/khmer_spoken/workspace/spoken_train_next.jsonl"
PRIOR2 = ROOT / "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
PRIOR3 = ROOT / "data/khmer_spoken/workspace/spoken_train_next3.jsonl"
OUT = ROOT / "data/khmer_spoken/workspace/spoken_train_next4.jsonl"
GATE = ROOT / "data/outputs/voice_training/2026-10-26-spoken-next/write_train_next.py"
LINES_PATH = Path(__file__).resolve().parent / "lines_draft.txt"

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the train pool after kp-2600. "
    "Original English line, checked against kp-001 through kp-2600. "
    "Licence unknown. Not gold. Not human. Pending native review. "
    "Not a weight update."
)
REVIEWER_NOTES = (
    "Synthetic English source only. No reference Khmer. "
    "review_status pending_native_review. Not gold. Not human."
)

EMOTIONS = [
    "neutral", "worried", "neutral", "happy", "tired",
    "worried", "neutral", "teasing", "tender", "neutral",
    "worried", "neutral", "happy", "tired", "neutral",
    "worried", "tender", "neutral", "happy", "worried",
]
HELPERS = [
    "srey", "dara", "lina", "vuthy", "nita",
    "bopha", "rith", "piseth", "sokha", "channary",
]
BLOCKS = [
    ("batik_vat", "dyer_sopheap", "dyer_to_apprentice", "apprentice_to_dyer", "casual"),
    ("palm_sugar_grove", "tapper_vy", "tapper_to_helper", "helper_to_tapper", "casual"),
    ("projection_booth", "projectionist_leng", "projectionist_to_assistant", "assistant_to_projectionist", "casual"),
    ("charcoal_mound", "burner_khim", "burner_to_helper", "helper_to_burner", "casual"),
    ("incense_bench", "maker_sothy", "maker_to_apprentice", "apprentice_to_maker", "casual"),
    ("durian_orchard", "grower_rany", "grower_to_picker", "picker_to_grower", "casual"),
    ("enamel_sign_shop", "painter_boran", "painter_to_apprentice", "apprentice_to_painter", "casual"),
    ("rice_huller", "miller_chay", "miller_to_operator", "operator_to_miller", "casual"),
    ("net_loft", "stitcher_mea", "stitcher_to_helper", "helper_to_stitcher", "casual"),
    ("hand_dug_well", "digger_oun", "digger_to_assistant", "assistant_to_digger", "casual"),
]


def _lines() -> list[str]:
    text = LINES_PATH.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def _gate():
    spec = importlib.util.spec_from_file_location("spoken_write_train_next", GATE)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load the prior distinctness gate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _drafts(lines: list[str]) -> list[dict]:
    if len(lines) != 200:
        raise SystemExit(f"expected 200 lines, got {len(lines)}")
    if len(BLOCKS) != 10:
        raise SystemExit("expected 10 situation blocks")
    drafts = []
    for block_index, (setting, expert, rel_out, rel_back, register) in enumerate(BLOCKS):
        for offset in range(20):
            helper = HELPERS[offset // 2]
            expert_speaks = offset % 2 == 0
            drafts.append({
                "kind": "new_situation",
                "emotion": EMOTIONS[offset],
                "speaker_id": expert if expert_speaks else helper,
                "listener_id": helper if expert_speaks else expert,
                "relationship": rel_out if expert_speaks else rel_back,
                "register": register,
                "setting": setting,
                "category": setting,
                "source_text": lines[block_index * 20 + offset].strip(),
            })
    return drafts


def _row(number: int, draft: dict) -> dict:
    return {
        "id": f"kp-{number:04d}",
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
            "source_file": "data/khmer_spoken/workspace/spoken_train_next4.jsonl",
            "licence": None,
            "not_for_gold": True,
            "not_for_weight_training": True,
            "locked_from_training": False,
            "scale_pool": "train_next4",
            "setting": draft["setting"],
            "expansion": "kp-2601-kp-2800",
            "created_on": "2026-10-28",
            "situation_kind": draft["kind"],
            "holdout": False,
            "human": False,
            "note": (
                "Synthetic draft. Distinct from kp-001 through kp-2600. "
                "Licence unknown. Not gold. Not human. Not a weight update."
            ),
        },
        "schema_version": SCHEMA_VERSION,
    }


def _load_existing(gate) -> tuple[set[str], list[set[str]], set[tuple[str, ...]], int]:
    scale_rows = [json.loads(line) for line in SCALE.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior_rows = [json.loads(line) for line in PRIOR.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior2_rows = [json.loads(line) for line in PRIOR2.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior3_rows = [json.loads(line) for line in PRIOR3.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row["id"] for row in scale_rows] != [f"kp-{index:03d}" for index in range(1, 2001)]:
        raise SystemExit("spoken_scale ids are not kp-001 through kp-2000")
    if [row["id"] for row in prior_rows] != [f"kp-{index:04d}" for index in range(2001, 2201)]:
        raise SystemExit("spoken_train_next ids are not kp-2001 through kp-2200")
    if [row["id"] for row in prior2_rows] != [f"kp-{index:04d}" for index in range(2201, 2401)]:
        raise SystemExit("spoken_train_next2 ids are not kp-2201 through kp-2400")
    if [row["id"] for row in prior3_rows] != [f"kp-{index:04d}" for index in range(2401, 2601)]:
        raise SystemExit("spoken_train_next3 ids are not kp-2401 through kp-2600")
    holdout_filled = 0
    for row in scale_rows:
        number = int(str(row["id"]).split("-")[1])
        if 1001 <= number <= 2000 and any(
            str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or [])
        ):
            holdout_filled += 1
    rows = scale_rows + prior_rows + prior2_rows + prior3_rows
    norms = {gate._norm(row["source_text"]) for row in rows}
    content = [gate._content(row["source_text"]) for row in rows]
    grams: set[tuple[str, ...]] = set()
    for row in rows:
        grams |= gate._grams(row["source_text"])
    return norms, content, grams, holdout_filled


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    gate = _gate()
    scale_before = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    prior_before = hashlib.sha256(PRIOR.read_bytes()).hexdigest()
    prior2_before = hashlib.sha256(PRIOR2.read_bytes()).hexdigest()
    prior3_before = hashlib.sha256(PRIOR3.read_bytes()).hexdigest()
    norms, content, grams, holdout_filled = _load_existing(gate)
    drafts = _drafts(_lines())
    problems = gate._reject(drafts, norms, content, grams)
    if problems:
        print(f"REJECT {len(problems)}")
        for item in problems[:80]:
            print(item)
        raise SystemExit("new rows are not distinct enough; nothing written")
    built = [_row(2600 + index, draft) for index, draft in enumerate(drafts, start=1)]
    if [row["id"] for row in built] != [f"kp-{index:04d}" for index in range(2601, 2801)]:
        raise SystemExit("ids are not kp-2601 through kp-2800")
    for row in built:
        if row["origin"] in {"human_authored", "human_reviewed", "human", "gold"}:
            raise SystemExit(f"{row['id']} origin is forbidden")
        if row["review_status"] != "pending_native_review" or row["license_type"] != "unknown":
            raise SystemExit(f"{row['id']} review or licence is wrong")
        if row["verified_by"] or row["approved_text"] or row["candidates"]:
            raise SystemExit(f"{row['id']} looks approved or filled")
        if row["metadata"].get("human") is not False or row["metadata"].get("not_for_gold") is not True:
            raise SystemExit(f"{row['id']} is marked human or gold")
        number = int(row["id"].split("-")[1])
        if 1001 <= number <= 2000:
            raise SystemExit("holdout id in the new file")
    lines = [json.dumps(row, ensure_ascii=False) for row in built]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(OUT.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, OUT)
    scale_after = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    prior_after = hashlib.sha256(PRIOR.read_bytes()).hexdigest()
    prior2_after = hashlib.sha256(PRIOR2.read_bytes()).hexdigest()
    prior3_after = hashlib.sha256(PRIOR3.read_bytes()).hexdigest()
    if (
        scale_after != scale_before
        or prior_after != prior_before
        or prior2_after != prior2_before
        or prior3_after != prior3_before
    ):
        raise SystemExit("a compared source file changed during the write")
    if holdout_filled != 0:
        raise SystemExit("holdout_filled is not 0")
    settings = Counter(draft["setting"] for draft in drafts)
    print(json.dumps({
        "wrote": str(OUT.relative_to(ROOT)),
        "rows": len(built),
        "id_first": built[0]["id"],
        "id_last": built[-1]["id"],
        "settings": dict(settings),
        "licence": "unknown",
        "review_status": "pending_native_review",
        "origin": "synthetic",
        "human": False,
        "gold": False,
        "distinct_against": "kp-001–kp-2600",
        "holdout_filled_on_scale": holdout_filled,
        "scale_sha256_unchanged": scale_after,
        "train_next_sha256_unchanged": prior_after,
        "train_next2_sha256_unchanged": prior2_after,
        "train_next3_sha256_unchanged": prior3_after,
        "weights_started": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
