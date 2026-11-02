"""LLM lab CLI — dataset, spoken status, training dry-run."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claynext.cli import cmd_dataset
from claynext.cli.common import die
from claynext.utils.paths import DATA_DIR, KHMER_SPOKEN_DIR, ensure_data_dirs


def _cmd_spoken_status(_: argparse.Namespace) -> int:
    ensure_data_dirs()
    workspace = KHMER_SPOKEN_DIR / "workspace"
    files = sorted(workspace.glob("spoken*.jsonl")) if workspace.is_dir() else []
    report: dict = {"data_dir": str(DATA_DIR), "spoken_files": []}
    for path in files:
        filled = empty = holdout_filled = 0
        last = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rid = str(row.get("id") or "")
            try:
                num = int(rid.split("-")[-1])
            except ValueError:
                continue
            has = any(str((c or {}).get("text") or "").strip() for c in (row.get("candidates") or []))
            if 1001 <= num <= 2000:
                if has:
                    holdout_filled += 1
                continue
            if has:
                filled += 1
                last = rid
            else:
                empty += 1
        report["spoken_files"].append(
            {
                "path": str(path.relative_to(DATA_DIR.parent)),
                "filled": filled,
                "empty": empty,
                "holdout_filled": holdout_filled,
                "last_filled": last,
            }
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _cmd_train_dry_run(args: argparse.Namespace) -> int:
    from claynext.models.training.trainer import start

    path = Path(args.config)
    if not path.is_file():
        die(f"config not found: {path}")
    result = start(path, approval=bool(args.approval))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") in {"dry_run", "refused"} else 1


def _cmd_fixture(args: argparse.Namespace) -> int:
    from dataclasses import asdict

    from claynext.models.training.spoken_fixture import SpokenKhmerFixture

    if not args.id and not args.source:
        die("pass --id or --source")
    fixture = SpokenKhmerFixture()
    out = fixture.lookup(row_id=args.id or "", source=args.source or "")
    print(json.dumps(asdict(out), ensure_ascii=False, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claynext-llm",
        description="Claynext LLM Lab: datasets, spoken Khmer collection, training dry-run.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    cmd_dataset.add_parser(sub)

    spoken = sub.add_parser("spoken-status", help="Count filled vs empty spoken rows (holdout separate)")
    spoken.set_defaults(func=_cmd_spoken_status)

    train = sub.add_parser("train-dry-run", help="Validate a training config; refuses weight start on this machine")
    train.add_argument("config", help="Path to a YAML under src/claynext/models/training/configs/")
    train.add_argument("--approval", action="store_true", help="Pass approval=true (still refuses 3B/7B/8B/14B here)")
    train.set_defaults(func=_cmd_train_dry_run)

    fix = sub.add_parser("fixture", help="Lookup a stored Jev line from the spoken fixture (not a fine-tune)")
    fix.add_argument("--id", help="Row id such as kp-001")
    fix.add_argument("--source", help="Exact English source string")
    fix.set_defaults(func=_cmd_fixture)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
