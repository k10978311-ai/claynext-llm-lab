# Spoken Khmer fixture lookup

This is a test double. It returns a stored Jev line from the approved SFT export when the caller passes that row's id or the exact source string. It is not a trained language model and it did not update any weights.

| Field | Value |
| --- | --- |
| Code | `src/claynext/models/training/spoken_fixture.py` |
| Model id | `spoken-khmer-jev-lookup-20261026-b` |
| Rows | `sft-train-approved.jsonl` — 758 |
| Ids | kp-001–kp-758 |
| Split | train |
| Licence | unknown |
| owner_training_approved | true |
| Owner grant | `data/khmer_spoken/versions/owner-licence-grant-20261026/` |
| External licence | none recorded. This grant is not CC-BY. |
| Promotion | not_promoted |
| Weights | none written, none uploaded |
| chrF / COMET / human | not measured |

## Can do

- Look up the stored Jev Khmer line for an approved train id or its exact source string.

## Cannot do

- Free generation. An unknown source returns `source is not in the test set` and an empty line.
- Serve holdout ids kp-1001–kp-2000. Those ids are refused.
- 7B or 14B inference. This artifact has no weights.
- 3B, 7B, 8B, or 14B fine-tuning. On this 16 GB M4, `trainer.start` still refuses those configs when `approval=True`. `started` stays false. A refusal is not a fine-tune.
- Promotion. `evaluate_promotion` stays `not_promoted` without a human review that passes the gate.

The open file `data/khmer_spoken/versions/translate-sft-spoken-20261026/sft.jsonl` is not this card's corpus and was not rewritten.
