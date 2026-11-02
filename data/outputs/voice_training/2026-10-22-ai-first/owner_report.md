# AI-first spoken drafts — 2026-10-22

Gemini ran. No weights were written. Nothing was marked reviewed or gold.

## Drafts

- Source seed: `src/claynext/prompts/evaluations/khmer_pronoun_cases.jsonl` (100 existing pending lines).
- Source file: `data/khmer_spoken/fixtures/dialogue_100.jsonl` (100 rows, no Gemini candidates, licence `unknown`).
- AI output: `data/khmer_spoken/workspace/candidates.jsonl`.
- 55 rows (`kp-001` through `kp-055`) have 3 Gemini candidates each. Model: `gemini-flash-latest`.
- 45 rows still have only the unverified stub.
- All 100 rows are `pending_native_review`. `verified_by` is empty. Licence type is `unknown`.

## Why it stopped

`kp-056` failed with “No available gemini API keys” while 4 Gemini keys were still enabled. They were cooling. The runner was stopped so it would not keep retrying on that pool. No key was written down.

## Train gate

`export_gold_version` wrote `data/khmer_spoken/versions/ai-draft-not-gold-20261022/dialogue.jsonl` at 0 bytes. Manifest count is 0. 100 rows were rejected. Local LoRA jobs are all `refused`. Vertex was not called.

## Review later

Read the 55 candidate triples in `data/khmer_spoken/workspace/candidates.jsonl`. Weight training still waits on that review and a real licence.
