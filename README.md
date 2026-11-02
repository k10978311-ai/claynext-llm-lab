# Claynext LLM Lab

Dedicated project for **Khmer spoken datasets**, Gemini teacher + Jev ranking,
benchmarks, and LLM training dry-runs.

This is a separate codebase from Claynext Studio (the media / dubbing app).
There is **no sync bridge** between the two. Dataset and model-training work
happens only here.

## Layout

| Area | Path |
|------|------|
| Spoken Khmer data | `data/khmer_spoken/` |
| Fill / export scripts | `data/outputs/voice_training/` |
| Dialogue datasets | `src/claynext/models/datasets/` |
| Spoken schema + Gemini teacher | `src/claynext/models/khmer_spoken/` |
| Jev ranker + key pool | `src/claynext/models/jev_decisions.py`, `llm_keys.py` |
| Training dry-run + fixture | `src/claynext/models/training/` |
| Benchmarks / promotion gate | `src/claynext/models/benchmarks/` |
| Khmer localization lexicons | `src/claynext/models/khmer_localization/` |
| Voice-training stubs | `src/claynext/voice_training/` |
| Docs | `docs/khmer-platform/` |

## Setup

```bash
cd ~/Desktop/claynext-llm-lab
uv sync
export PYTHONPATH=src
```

API keys: set `GEMINI_API_KEY` / `TYPESAFE_API_KEY`, or store them in local
`data/lab.db` (gitignored). Do not commit keys.

## Commands

```bash
uv run claynext-llm dataset --help
uv run claynext-llm spoken-status
uv run claynext-llm train-dry-run src/claynext/models/training/configs/sft_lora_3b.yaml
uv run claynext-llm fixture --id kp-001
```

## Rules

- Licence on spoken rows stays `unknown` unless a sidecar says otherwise.
- Holdout ids kp-1001–kp-2000 stay empty of training candidates.
- `trainer.start` may dry-run or refuse; do not claim a fine-tune without weights.
- Promotion stays closed until native review exists.
