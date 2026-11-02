# Claynext LLM Lab — agent rules

Dedicated LLM / dataset / training project. Not Claynext Studio.

1. Do not add PySide6 Studio UI, dubbing, or FFmpeg pipelines.
2. Do not add sync or export scripts that pull from or push to Studio.
3. Put generated artefacts under `data/` only.
4. Never commit API keys, `data/lab.db`, or `.env` files.
5. `trainer.start` may dry-run or refuse; do not claim a fine-tune without weights on disk.
6. Holdout ids kp-1001–kp-2000 stay empty unless the owner changes the lock.
7. Treat this repo as the only home for spoken-dataset and training jobs.
