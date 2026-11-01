from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


MODEL_PATH = Path(os.getenv(
    "MODEL_PATH", str(PROJECT_ROOT / "models" / "logistic_regression_classifier.joblib")
))
INTENT_LABELS_PATH = Path(os.getenv(
    "INTENT_LABELS_PATH", str(PROJECT_ROOT / "models" / "intent_labels.json")
))
MANIFEST_PATH = Path(os.getenv(
    "MODEL_MANIFEST_PATH", str(PROJECT_ROOT / "models" / "model_manifest.json")
))
ENCODER_ID = os.getenv(
    "ENCODER_ID", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
ENCODER_REVISION = os.getenv("ENCODER_REVISION", "").strip() or None
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.50"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
DEVICE = os.getenv("MODEL_DEVICE", "cpu")
AUTO_LOAD_MODEL = env_bool("AUTO_LOAD_MODEL", True)

if not 0.0 <= CONFIDENCE_THRESHOLD <= 1.0:
    raise ValueError("CONFIDENCE_THRESHOLD debe estar entre 0 y 1.")
if MAX_TEXT_LENGTH < 3:
    raise ValueError("MAX_TEXT_LENGTH debe ser al menos 3.")
