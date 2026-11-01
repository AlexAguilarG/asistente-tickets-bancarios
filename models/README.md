# Artefactos del modelo

- `intent_labels.json`: diccionario ID (0–76) -> nombre canónico, extraído del proyecto de Actividad 5.
- `logistic_regression_classifier.joblib`: se copia desde `Actividad5/modelos/` mediante el notebook `notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb`. No se incluye en el ZIP inicial porque no estaba entre los archivos compartidos en esta conversación.
- `model_manifest.json`: se genera desde Colab con versiones del entorno y metadatos de exportación.

El `.joblib` es un artefacto serializado confiable del propio proyecto. No cargues archivos joblib recibidos de terceros: deserializar archivos pickle/joblib no confiables puede ejecutar código.
