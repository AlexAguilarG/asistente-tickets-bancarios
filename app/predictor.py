from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)


class TicketClassifier:
    """Pipeline de inferencia: texto -> MiniLM normalizado -> Regresión Logística."""

    def __init__(
        self,
        classifier: Any,
        encoder: Any,
        label_names: dict[int, str],
        encoder_id: str,
        confidence_threshold: float = 0.50,
    ) -> None:
        if not hasattr(classifier, "predict_proba"):
            raise TypeError("El artefacto no contiene un clasificador compatible con predict_proba.")
        self.classifier = classifier
        self.encoder = encoder
        self.label_names = label_names
        self.encoder_id = encoder_id
        self.confidence_threshold = confidence_threshold
        self.model_name = "logistic_regression"

        classes = [int(x) for x in getattr(classifier, "classes_", [])]
        if not classes:
            raise ValueError("El clasificador no contiene clases entrenadas.")
        missing = [class_id for class_id in classes if class_id not in label_names]
        if missing:
            raise ValueError(f"Faltan nombres para las clases: {missing[:10]}")

    @classmethod
    def load_from_files(
        cls,
        model_path: Path,
        labels_path: Path,
        manifest_path: Path,
        confidence_threshold: float,
        device: str = "cpu",
        encoder_id_override: str | None = None,
    ) -> "TicketClassifier":
        if not model_path.is_file():
            raise FileNotFoundError(
                f"No se encontró el modelo {model_path}. Ejecuta el notebook "
                "notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb para copiar el artefacto real."
            )
        if not labels_path.is_file():
            raise FileNotFoundError(f"No se encontró el catálogo de intenciones: {labels_path}")

        # joblib/pickle solo debe abrirse si el artefacto procede de una fuente confiable.
        bundle = joblib.load(model_path)
        if isinstance(bundle, dict) and "classifier" in bundle:
            classifier = bundle["classifier"]
            bundle_encoder_id = bundle.get("encoder_id")
            bundle_labels = bundle.get("label_names")
        else:
            classifier = bundle
            bundle_encoder_id = None
            bundle_labels = None

        labels_raw = json.loads(labels_path.read_text(encoding="utf-8"))
        labels = {int(key): str(value) for key, value in labels_raw.items()}
        if bundle_labels and len(bundle_labels) == 77:
            labels = {i: str(name) for i, name in enumerate(bundle_labels)}

        manifest: dict[str, Any] = {}
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        encoder_id = (
            encoder_id_override
            or bundle_encoder_id
            or manifest.get("encoder_id")
            or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        encoder_revision = manifest.get("encoder_revision")

        # Importación diferida: los tests de API no necesitan descargar PyTorch/transformers.
        from sentence_transformers import SentenceTransformer

        kwargs: dict[str, Any] = {"device": device}
        if encoder_revision:
            kwargs["revision"] = encoder_revision
        encoder = SentenceTransformer(encoder_id, **kwargs)

        expected_sklearn = manifest.get("versions", {}).get("scikit-learn")
        try:
            import sklearn
            actual_sklearn = sklearn.__version__
            if expected_sklearn and expected_sklearn != actual_sklearn:
                warnings.warn(
                    "La versión de scikit-learn del contenedor ("
                    f"{actual_sklearn}) difiere de la usada al exportar el modelo "
                    f"({expected_sklearn}). Para máxima reproducibilidad instala "
                    "requirements-runtime.lock generado desde Colab.",
                    RuntimeWarning,
                )
                logger.warning("Versiones sklearn distintas: runtime=%s export=%s", actual_sklearn, expected_sklearn)
        except Exception as exc:  # pragma: no cover - diagnóstico, no bloquea inferencia
            logger.warning("No fue posible comparar versión de scikit-learn: %s", exc)

        return cls(
            classifier=classifier,
            encoder=encoder,
            label_names=labels,
            encoder_id=encoder_id,
            confidence_threshold=confidence_threshold,
        )

    def predict(self, text: str) -> dict[str, Any]:
        embeddings = self.encoder.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        features = np.asarray(embeddings, dtype=np.float32)
        if features.ndim != 2 or features.shape[0] != 1:
            raise RuntimeError("El encoder devolvió una representación con dimensiones inesperadas.")

        probabilities = np.asarray(self.classifier.predict_proba(features))[0]
        if probabilities.ndim != 1 or not np.isfinite(probabilities).all():
            raise RuntimeError("El clasificador devolvió probabilidades inválidas.")

        class_ids = np.asarray(self.classifier.classes_, dtype=int)
        best_position = int(np.argmax(probabilities))
        class_id = int(class_ids[best_position])
        confidence = float(probabilities[best_position])
        needs_review = confidence < self.confidence_threshold

        return {
            "model_name": self.model_name,
            "predicted_intent_id": class_id,
            "predicted_intent": self.label_names[class_id],
            "confidence": confidence,
            "confidence_threshold": self.confidence_threshold,
            "decision": "human_review" if needs_review else "suggestion",
            "requires_human_review": needs_review,
            "priority_assigned": None,
            "priority_note": (
                "No se asigna prioridad automáticamente: esta versión solo clasifica intención. "
                "La prioridad debe establecerse mediante reglas aprobadas por Operación."
            ),
            "disclaimer": (
                "Prototipo académico basado en BANKING77 traducido; la confianza no está calibrada "
                "para producción ni validada con tickets reales de un banco mexicano."
            ),
        }
