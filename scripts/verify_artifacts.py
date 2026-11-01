from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "models" / "logistic_regression_classifier.joblib",
    ROOT / "models" / "intent_labels.json",
    ROOT / "models" / "model_manifest.json",
    ROOT / "requirements-runtime.lock",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file() or path.stat().st_size == 0]

labels_path = ROOT / "models" / "intent_labels.json"
if labels_path.is_file():
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if len(labels) != 77:
        missing.append("models/intent_labels.json (debe contener 77 intenciones)")

if missing:
    print("Faltan artefactos necesarios para el despliegue reproducible:")
    for item in missing:
        print(" -", item)
    print("Ejecuta notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb para exportar el modelo y fijar dependencias.")
    sys.exit(1)

print("Artefactos y lock disponibles. El proyecto está listo para construir la imagen.")
