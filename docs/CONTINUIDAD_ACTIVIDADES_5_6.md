# Continuidad técnica de las Actividades 5 y 6

## Pipeline conservado

- Dataset: `DeepPavlov/banking77-translated`, configuración española (`es`); benchmark de consulta bancaria traducida, no histórico de tickets de un banco mexicano.
- Texto de entrada: `text_gemma` en la preparación del dataset y texto limpio del pipeline de inferencia.
- Etiqueta: `label`, IDs 0–76, catálogo canónico de 77 intenciones.
- Encoder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, embeddings normalizados.
- Modelo candidato: Regresión Logística multiclase con `predict_proba`.
- Comparador previo: Random Forest. No se incluye en el backend de despliegue porque Regresión Logística fue el candidato seleccionado para esta fase.

## Resultados offline reportados al cierre de Actividad 6

| Indicador | Regresión Logística | Random Forest |
|---|---:|---:|
| F1 macro medio CV (5 folds) | 0.874979 | 0.843913 |
| Accuracy test | 0.887792 | 0.862857 |
| Precision macro | 0.891960 | 0.868230 |
| Recall macro | 0.887792 | 0.862857 |
| F1 macro test | 0.887280 | 0.861592 |
| ROC-AUC macro OVR | 0.997284 | 0.994047 |

Comparación pareada offline en 1,925 ejemplos: 90 casos acertados solo por Regresión Logística, 42 acertados solo por Random Forest; McNemar exacta `p=3.573574653630987e-05`. El intervalo bootstrap pareado del 95% para Δ accuracy (LR − RF) fue aproximadamente `[0.0130, 0.0364]`.

En el análisis exploratorio de umbral, 0.50 produjo 84.4% de cobertura y 95.6% de exactitud selectiva en el conjunto de prueba; 0.90 obtuvo 36.9% de cobertura y 99.4% de exactitud selectiva. Estos valores se reportan como diagnóstico offline. No son un umbral calibrado ni una política aprobada para producción.

## Trazabilidad MLflow

- Tracking URI utilizada en Colab: backend SQLite `mlflow.db` dentro de la carpeta Actividad5 de Google Drive.
- Run ID de evaluación: `b4b690a047aa47a48c1071126d3e0770`.
- En esa ejecución se registraron 7 artefactos en la primera operación y 17 artefactos complementarios bajo `evaluation_validation`.

## Decisión para despliegue

Se conserva únicamente el clasificador de Regresión Logística para inferencia. El encoder MiniLM forma parte del pipeline de inferencia aunque sus pesos no estén dentro del `.joblib`; se descarga desde Hugging Face en el primer arranque. El artefacto de clasificador debe exportarse desde el Drive del proyecto mediante el notebook de Colab de este repositorio.

La aplicación no asigna prioridad. Esa capacidad requeriría reglas de negocio aprobadas o un modelo adicional entrenado y validado con etiquetas de prioridad.
