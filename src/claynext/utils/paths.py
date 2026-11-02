"""Lab data roots. All artefacts stay under ``data/``."""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
OUTPUTS_DIR = DATA_DIR / "outputs"
CACHE_DIR = DATA_DIR / "cache"
LOGS_DIR = DATA_DIR / "logs"
DATASETS_DIR = DATA_DIR / "datasets"
VOICE_DATASETS_DIR = DATA_DIR / "voice_datasets"
KHMER_SPOKEN_DIR = DATA_DIR / "khmer_spoken"

DATA_DIRS = (
    DATA_DIR,
    MODELS_DIR,
    OUTPUTS_DIR,
    CACHE_DIR,
    LOGS_DIR,
    DATASETS_DIR,
    VOICE_DATASETS_DIR,
    KHMER_SPOKEN_DIR,
)


def ensure_data_dirs() -> None:
    for folder in DATA_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
