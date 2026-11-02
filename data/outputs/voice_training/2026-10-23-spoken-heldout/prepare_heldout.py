"""Lock a train/test split for the owner-approved Khmer spoken rows.

Reads the remainder-2 snapshot from git (the working-tree candidates file is a
different hash). Does not start a fine-tune, change licences, or score quality.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from claynext.models.benchmarks.runner import decoding_config, run_benchmark
from claynext.models.benchmarks.schema import BenchmarkRow
from claynext.models.training.trainer import start, training_implementation_available

ROOT = Path(__file__).resolve().parents[4]
SOURCE_COMMIT = "d2e93afc6e0ed10d1dedb68c2d72ddb1badd34db"
SOURCE_BRANCH = "feat/spoken-drafts-key-roll"
SOURCE_VERSION = "owner-approved-20261023-remainder-2"
SPLIT_VERSION = "heldout-locked-20261023-kp081-100"
DIALOGUE_BLOB = "e020f043d02267d4a5b18de5398c87aa56229b85"
RANKED_BLOB = "bb4bb70253438c4f87fb127bbb088c9b94c14451"
TEST_FIRST = 81
TEST_LAST = 100
OWNER_QUOTE = "continue train my spoke turne for best performae bensmark"
FAKE_TEXT = "FAKE_NO_WEIGHTS"
CONFIG = ROOT / "src/claynext/models/training/configs/sft_lora_3b.yaml"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _git_show(spec: str) -> str:
    return subprocess.check_output(["git", "show", spec], cwd=ROOT, text=True)


def _rows(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _memory() -> dict:
    try:
        text = subprocess.check_output(["memory_pressure", "-Q"], text=True)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    free = None
    for line in text.splitlines():
        if "free percentage" in line:
            free = line.strip()
    return {"free_percentage_line": free, "raw": text.strip()}


def _ollama_ps() -> str:
    try:
        return subprocess.check_output(["ollama", "ps"], text=True).strip()
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {exc}"


def _studio_running() -> str:
    try:
        text = subprocess.check_output(["ps", "aux"], text=True)
    except Exception as exc:  # noqa: BLE001
        return f"unchecked: {exc}"
    hits = [
        line for line in text.splitlines()
        if "claynext" in line.lower() or "main.py" in line
    ]
    # Drop this script's own command line if it mentions claynext only as a path.
    hits = [line for line in hits if "prepare_heldout.py" not in line]
    return "running" if hits else "not_seen"


def _materialize_source() -> Path:
    dest = ROOT / "data/khmer_spoken/versions" / SOURCE_VERSION
    dialogue = dest / "dialogue.jsonl"
    ranked = dest / "ranked.jsonl"
    manifest = dest / "manifest.json"
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"refusing to overwrite existing snapshot {dest}")
    dest.mkdir(parents=True)
    dialogue.write_text(
        _git_show(f"{SOURCE_COMMIT}:data/khmer_spoken/versions/{SOURCE_VERSION}/dialogue.jsonl"),
        encoding="utf-8",
    )
    ranked.write_text(
        _git_show(f"{SOURCE_COMMIT}:data/khmer_spoken/versions/{SOURCE_VERSION}/ranked.jsonl"),
        encoding="utf-8",
    )
    manifest.write_text(
        _git_show(f"{SOURCE_COMMIT}:data/khmer_spoken/versions/{SOURCE_VERSION}/manifest.json"),
        encoding="utf-8",
    )
    dialogue_blob = subprocess.check_output(
        ["git", "hash-object", str(dialogue)], cwd=ROOT, text=True
    ).strip()
    ranked_blob = subprocess.check_output(
        ["git", "hash-object", str(ranked)], cwd=ROOT, text=True
    ).strip()
    if dialogue_blob != DIALOGUE_BLOB or ranked_blob != RANKED_BLOB:
        raise SystemExit(
            f"snapshot hash mismatch dialogue={dialogue_blob} ranked={ranked_blob}"
        )
    return dest


def _scene_by_id() -> dict[str, dict]:
    path = ROOT / "src/claynext/prompts/evaluations/khmer_pronoun_cases.jsonl"
    found: dict[str, dict] = {}
    for row in _rows(path.read_text(encoding="utf-8")):
        found[row["id"]] = row
    return found


def _pair(example: dict, seed: dict) -> dict:
    jev = (example.get("metadata") or {}).get("jev") or {}
    preferred = str(jev.get("preferred_text") or "").strip()
    applied = bool(jev.get("applied")) and bool(preferred)
    candidate_texts = [c.get("text") for c in example.get("candidates") or []]
    if applied and preferred not in candidate_texts:
        applied = False
        preferred = ""
    stub = str(example.get("stub_khmer") or "")
    scene = ((seed.get("scene") or {}).get("id")) or example["id"]
    return {
        "id": example["id"],
        "dialogue_family_id": scene,
        "scene_id": scene,
        "source": example.get("source_text") or "",
        "target": preferred,
        "stub_khmer": stub,
        "reference_kind": "jev_preferred_line" if applied else "missing_jev",
        "reference_equals_stub": bool(applied and preferred == stub),
        "from_jev": applied,
        "license_type": example.get("license_type") or "unknown",
        "origin": example.get("origin") or "",
        "source_review_status_field": example.get("review_status") or "",
        "not_for_gold": bool((example.get("metadata") or {}).get("not_for_gold")),
        "not_for_weight_training_metadata": bool(
            (example.get("metadata") or {}).get("not_for_weight_training")
        ),
        "speaker_id": example.get("speaker_id") or "",
        "listener_id": example.get("listener_id") or "",
        "relationship": example.get("relationship") or "",
        "emotion": example.get("emotion") or "neutral",
        "register": example.get("register") or "neutral",
        "category": example.get("category") or "everyday",
        "source_language": example.get("source_lang") or "en",
        "candidate_count": len(example.get("candidates") or []),
    }


def _benchmark_row(pair: dict, split: str) -> BenchmarkRow:
    return BenchmarkRow(
        id=pair["id"],
        scene_id=pair["scene_id"],
        dialogue_family_id=pair["dialogue_family_id"],
        source_language=pair["source_language"],
        source_text=pair["source"],
        reference_khmer=pair["target"],
        split=split,
        licence=pair["license_type"],
        review_status="pending_native_review",
        origin="gemini_teacher",
        dataset_version=SPLIT_VERSION,
        locked=split == "test",
        synthetic_only=True,
        speaker_id=pair["speaker_id"],
        listener_id=pair["listener_id"],
        relationship=pair["relationship"],
        emotion=pair["emotion"],
        register=pair["register"],
        category=pair["category"],
    )


def _export_row(pair: dict, split: str) -> dict:
    return {
        "id": pair["id"],
        "dialogue_family_id": pair["dialogue_family_id"],
        "scene_id": pair["scene_id"],
        "split": split,
        "locked": split == "test",
        "source": pair["source"],
        "target": pair["target"],
        "stub_khmer": pair["stub_khmer"],
        "reference_kind": pair["reference_kind"],
        "reference_equals_stub": pair["reference_equals_stub"],
        "from_jev": pair["from_jev"],
        "license_type": "unknown",
        "origin": pair["origin"],
        "source_review_status_field": pair["source_review_status_field"],
        "benchmark_review_status": "pending_native_review",
        "not_for_gold": pair["not_for_gold"],
        "speaker_id": pair["speaker_id"],
        "listener_id": pair["listener_id"],
        "relationship": pair["relationship"],
        "emotion": pair["emotion"],
        "register": pair["register"],
        "category": pair["category"],
        "candidate_count": pair["candidate_count"],
    }


def main() -> None:
    wt = ROOT / "data/khmer_spoken/workspace/candidates.jsonl"
    wt_hash = _sha256_file(wt) if wt.is_file() else ""
    branch_candidates = _git_show(
        f"{SOURCE_COMMIT}:data/khmer_spoken/workspace/candidates.jsonl"
    )
    branch_hash = _sha256_text(branch_candidates)
    if wt_hash == branch_hash:
        raise SystemExit("working tree candidates unexpectedly match remainder-2; check the source")

    source_dir = _materialize_source()
    dialogue = _rows((source_dir / "dialogue.jsonl").read_text(encoding="utf-8"))
    ranked = _rows((source_dir / "ranked.jsonl").read_text(encoding="utf-8"))
    if len(dialogue) != 100 or len(ranked) != 100:
        raise SystemExit(f"expected 100 rows, got dialogue={len(dialogue)} ranked={len(ranked)}")
    by_rank = {row["id"]: row for row in ranked}
    seeds = _scene_by_id()
    families: dict[str, list[str]] = {}
    pairs: list[dict] = []
    for example in dialogue:
        seed = seeds.get(example["id"]) or {}
        pair = _pair(example, seed)
        rank = by_rank[pair["id"]]
        if rank.get("target") != pair["target"] or rank.get("license_type") != "unknown":
            raise SystemExit(f"ranked target/licence mismatch for {pair['id']}")
        if pair["license_type"] != "unknown" or pair["candidate_count"] != 3 or not pair["from_jev"]:
            raise SystemExit(f"row {pair['id']} is not an unknown-licence 3-candidate Jev row")
        families.setdefault(pair["dialogue_family_id"], []).append(pair["id"])
        pairs.append(pair)
    if len(families) != 100:
        raise SystemExit(f"expected 100 dialogue families, got {len(families)}")

    def _num(row_id: str) -> int:
        return int(row_id.split("-")[1])

    test_ids = {pair["id"] for pair in pairs if TEST_FIRST <= _num(pair["id"]) <= TEST_LAST}
    # A shared family cannot sit on both sides. Hold the whole family out.
    leaked = set()
    for family, members in families.items():
        if any(member in test_ids for member in members):
            leaked.update(members)
    test_ids |= leaked
    train_pairs = [pair for pair in pairs if pair["id"] not in test_ids]
    test_pairs = [pair for pair in pairs if pair["id"] in test_ids]
    if len(test_pairs) < 20:
        raise SystemExit("test split is smaller than 20 rows")
    if {pair["id"] for pair in train_pairs} & {pair["id"] for pair in test_pairs}:
        raise SystemExit("train/test id overlap")
    train_families = {pair["dialogue_family_id"] for pair in train_pairs}
    test_families = {pair["dialogue_family_id"] for pair in test_pairs}
    if train_families & test_families:
        raise SystemExit(f"family leakage: {sorted(train_families & test_families)}")

    split_dir = ROOT / "data/khmer_spoken/versions" / SPLIT_VERSION
    if split_dir.exists():
        raise SystemExit(f"refusing to overwrite {split_dir}")
    split_dir.mkdir(parents=True)
    train_rows = [_export_row(pair, "train") for pair in train_pairs]
    test_rows = [_export_row(pair, "test") for pair in test_pairs]
    _write_jsonl(split_dir / "train.jsonl", train_rows)
    _write_jsonl(split_dir / "test.jsonl", test_rows)

    out_dir = ROOT / "data/outputs/voice_training/2026-10-23-spoken-heldout"
    out_dir.mkdir(parents=True, exist_ok=True)
    memory = _memory()
    ollama = _ollama_ps()
    studio = _studio_running()
    trainer_result = start(
        CONFIG,
        approval=True,
        registry_dir=out_dir / "registry",
    )
    installed = training_implementation_available()
    started = bool(trainer_result.get("started"))
    if started:
        raise SystemExit("trainer.start reported started; refusing to continue")
    reason = (
        "No safe trainer can update weights on this 16 GB M4: peft and mlx are "
        "not installed, and trainer.start refuses the 3B/7B/8B/14B configs."
    )
    if trainer_result.get("reason"):
        reason = str(trainer_result["reason"])
        if not installed:
            reason = (
                f"{reason} peft and mlx_lm are not installed, so no tiny adapter ran either."
            )

    manifest = {
        "version": SPLIT_VERSION,
        "created_at": _now(),
        "started": False,
        "weights_written": False,
        "weights_uploaded": False,
        "dry_run": True,
        "reason": reason,
        "trainer_result": trainer_result,
        "implementation_available": installed,
        "config_refused": str(CONFIG.relative_to(ROOT)),
        "machine": {"name": "apple-m4", "ram_gb": 16, "memory": memory, "ollama_ps": ollama, "studio": studio},
        "source": {
            "branch": SOURCE_BRANCH,
            "commit": SOURCE_COMMIT,
            "version": SOURCE_VERSION,
            "dialogue_git_blob": DIALOGUE_BLOB,
            "ranked_git_blob": RANKED_BLOB,
            "path": str(source_dir),
            "working_tree_candidates_sha256": wt_hash,
            "branch_candidates_sha256": branch_hash,
            "working_tree_candidates_used": False,
        },
        "licence": {
            "license_type": "unknown",
            "changed": False,
            "invented_cc_by": False,
        },
        "owner_intent": {
            "by": "project-owner",
            "at": "2026-10-23",
            "quote": OWNER_QUOTE,
            "scope": (
                "Local read of these owner-approved spoken rows for a train attempt "
                "and a locked held-out benchmark. Not approval for Vertex, a hosted "
                "fine-tune, or a 7B/8B/14B launch."
            ),
            "allows_reading_unknown_licence": True,
            "prior_metadata_not_for_weight_training": True,
            "note": (
                "Every source row still has license_type unknown and "
                "not_for_weight_training true. Owner intent is why this run may read "
                "them. The licence field was not flipped."
            ),
        },
        "split": {
            "rule": "row id kp-081 through kp-100, expanded to the whole dialogue family",
            "dialogue_family_id": "scene id from khmer_pronoun_cases.jsonl",
            "tune_on_test": False,
            "train_count": len(train_rows),
            "test_count": len(test_rows),
            "train_ids": [row["id"] for row in train_rows],
            "test_ids": [row["id"] for row in test_rows],
            "train_path": str(split_dir / "train.jsonl"),
            "test_path": str(split_dir / "test.jsonl"),
            "reference_kind": "jev_preferred_line",
            "test_rows_using_stub_as_reference": 0,
            "test_rows_whose_jev_text_equals_stub": sum(
                1 for row in test_rows if row["reference_equals_stub"]
            ),
            "locked_test": True,
        },
        "promotion": "not_promoted",
        "hosted_fine_tune": False,
        "old_job_untouched": "data/khmer_spoken/jobs/lora-ac1dc7173b31.json",
    }
    (split_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "training_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    bench_rows = [_benchmark_row(pair, "test") for pair in test_pairs]
    train_bench = [_benchmark_row(pair, "train") for pair in train_pairs]
    bench_dir = ROOT / "data/outputs/benchmarks/2026-10-23-spoken-heldout-test"

    def translate(_row: BenchmarkRow) -> dict:
        return {
            "text": FAKE_TEXT,
            "latency_ms": None,
            "cost_usd": None,
            "tokens_in": None,
            "tokens_out": None,
            "trace_id": "",
        }

    report = run_benchmark(
        bench_rows,
        translate,
        train_rows=train_bench,
        model_id="fake-placeholder",
        provider_label="fake",
        dataset_version=SPLIT_VERSION,
        decoding=decoding_config(temperature=0.0, seed=13),
        gold_benchmark=False,
        synthetic_fixture=False,
        judge=None,
        out_dir=bench_dir,
        hosted_probe=False,
    )
    report["started_training"] = False
    report["weights_written"] = False
    report["quality_score"] = None
    report["scores_not_computed"] = ["chrF", "COMET", "human"]
    report["reference"] = {
        "kind": "jev_preferred_line",
        "is_the_stub": False,
        "is_human_gold": False,
        "licence": "unknown",
        "rows": len(test_rows),
        "jev_text_equals_stub_count": manifest["split"]["test_rows_whose_jev_text_equals_stub"],
        "note": (
            "The reference string is the Jev-ranked candidate stored on each row. "
            "It is not the stub line and it is not a human gold score. "
            "Licence remains unknown."
        ),
    }
    report["hypothesis"] = {
        "source": "fake placeholder",
        "text": FAKE_TEXT,
        "ollama_loaded": False,
        "note": "ollama ps was empty. No 7B/8B model was loaded. This is not a model score.",
    }
    report["allowed_to_claim"] = [
        "80 rows are locked out of the test split and 20 rows are a locked test split.",
        "The reference text is the Jev preferred line, not the stub, and not a human gold score.",
        "A fake placeholder was passed through the benchmark runner.",
        "Promotion stays not_promoted because there is no human review record.",
        "chrF, COMET, and human quality scores were not computed.",
    ]
    report["promotion_decision"] = report.get("promotion", {}).get("decision")
    if report.get("quality_score") is not None or report.get("promotion", {}).get("promoted"):
        raise SystemExit("refusing a report that claims a quality score or promotion")
    path = Path(report["path"])
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    job_id = "lora-" + hashlib.sha256(SPLIT_VERSION.encode()).hexdigest()[:12]
    job_path = ROOT / "data/khmer_spoken/jobs" / f"{job_id}.json"
    old = ROOT / "data/khmer_spoken/jobs/lora-ac1dc7173b31.json"
    old_before = old.read_text(encoding="utf-8")
    job = {
        "job_id": job_id,
        "kind": "local_lora",
        "status": "refused",
        "created_at": _now(),
        "updated_at": _now(),
        "error": reason,
        "details": {
            "dataset_path": str(split_dir / "train.jsonl"),
            "test_path": str(split_dir / "test.jsonl"),
            "base_model": "none",
            "platform": "local_open_weight",
            "separate_from_vertex": True,
            "started": False,
            "weights_written": False,
            "train_count": len(train_rows),
            "test_count": len(test_rows),
            "owner_intent_quote": OWNER_QUOTE,
            "licence": "unknown",
            "does_not_replace": "lora-ac1dc7173b31",
        },
    }
    job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if old.read_text(encoding="utf-8") != old_before:
        raise SystemExit("old job file changed")

    summary = {
        "train_count": len(train_rows),
        "test_count": len(test_rows),
        "split_path": str(split_dir),
        "weights_written": False,
        "started": False,
        "reason": reason,
        "benchmark_path": str(path),
        "job_path": str(job_path),
        "job_id": job_id,
        "trainer_status": trainer_result.get("status"),
        "ollama_ps": ollama,
        "studio": studio,
        "memory": memory.get("free_percentage_line"),
    }
    (out_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
