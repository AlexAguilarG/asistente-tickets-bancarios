# Documento de validación y pruebas del despliegue

## 1. Objetivo

Verificar que la aplicación integra frontend, API y pipeline de inferencia, procesa entradas válidas y rechaza solicitudes fuera del contrato. Esta validación de software es distinta de la evaluación offline del clasificador realizada en Actividad 6.

## 2. Base del modelo heredado

El backend reutiliza el encoder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` y el clasificador de Regresión Logística entrenado con 77 intenciones. Los resultados offline ya documentados son: accuracy 0.8878, F1 macro 0.8873 y ROC-AUC macro OVR 0.9973 en el benchmark BANKING77 traducido.

El benchmark no equivale a tickets reales de una institución bancaria mexicana. La aplicación expone una sugerencia de intención; no procesa operaciones y no asigna prioridad.

## 3. Pruebas automatizadas incluidas

| ID | Caso | Resultado esperado |
|---|---|---|
| API-01 | `GET /healthz` | HTTP 200, servicio activo |
| API-02 | `GET /readyz` con predictor cargado | HTTP 200, `model_loaded=true` |
| API-03 | `POST /api/predict` con texto válido | HTTP 200 y campos de intención/confianza |
| API-04 | Texto vacío o espacios | HTTP 422 |
| API-05 | Texto menor a 3 caracteres | HTTP 422 |
| API-06 | Campo adicional no permitido | HTTP 422 |
| API-07 | Modelo no cargado | HTTP 503, sin simular una predicción |
| API-08 | Texto superior a 5,000 caracteres | HTTP 422 |

Los tests de API utilizan un predictor simulado para probar el contrato HTTP sin cargar pesos ni descargar MiniLM. No sustituyen una prueba de inferencia real con el artefacto serializado.

## 4. Ejecutar pruebas automatizadas

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## 5. Prueba local integrada con Docker

Una vez exportado el artefacto desde Colab:

```bash
python scripts/verify_artifacts.py
docker build -t asistente-tickets:1.0.0 .
docker run --rm -p 8080:8080 -e CONFIDENCE_THRESHOLD=0.50 -v tickets-hf-cache:/home/app/.cache/huggingface asistente-tickets:1.0.0
```

Prueba `/healthz`, `/readyz`, `/docs`, `/` y `POST /api/predict`. Registrar en la evidencia de ejecución: versión de Docker, hash/tag de la imagen, fecha, tiempo de carga inicial, latencia de cada caso, código HTTP y resultado. No publicar datos de cliente.

## 6. Casos extremos y controles

- Texto vacío, solo espacios, muy corto o mayor a 5,000 caracteres.
- Entrada con acentos, ñ, signos, saltos de línea y caracteres Unicode.
- Entrada no textual, JSON inválido o campos inesperados.
- Artefacto `.joblib` ausente o corrupto: `/readyz` no debe indicar readiness.
- Error de descarga o inaccesibilidad de Hugging Face: servicio vivo, pero no listo para inferencia.
- Confianza menor al umbral: respuesta marcada `requires_human_review=true`.
- Probabilidad inválida o no finita: la solicitud no debe devolver una intención espuria.
- Primer arranque sin caché y arranques posteriores con caché.

## 7. Resultados comprobados y pendientes

| Evidencia | Estado al preparar este paquete |
|---|---|
| Estructura FastAPI, endpoints y frontend | Implementados en el repositorio |
| Tests de contrato API con predictor simulado | Pendientes de ejecución final en el entorno del usuario; se incluyen para ejecutar con pytest |
| Artefacto real `logistic_regression_classifier.joblib` | No estaba entre los archivos compartidos; exportación pendiente desde Drive/Colab |
| Inferencia real con MiniLM + clasificador | Pendiente del artefacto y descarga del encoder |
| Construcción de imagen Docker | Pendiente; el entorno de preparación no tiene Docker Engine |
| Ejecución del contenedor local | Pendiente en Docker Desktop del usuario |
| Despliegue Cloud Run | Manual documentado; no se ha desplegado |
| Prueba con tickets reales mexicanos | Pendiente de autorización, anonimización y validación de etiquetas |

No se reportan como realizados los pasos cuya evidencia no se ha producido.

## 8. Criterios para aceptar una demo local

1. Imagen construida sin error desde el Dockerfile.
2. Contenedor permanece en estado healthy.
3. `/healthz` responde 200 y `/readyz` responde 200 después de cargar el modelo.
4. Frontend puede enviar una solicitud a `/api/predict` y recibe un JSON válido.
5. Los casos de entrada inválida devuelven 422; modelo ausente devuelve 503.
6. Texto no queda registrado en logs.
7. Se identifica que el umbral 0.50 es experimental y que la prioridad no está automatizada.

## 9. Evidencias a capturar

- Terminal mostrando `docker build` completado y tag de imagen.
- `docker ps` y health status.
- Frontend funcionando con frase sintética.
- Swagger `/docs` mostrando `POST /api/predict`.
- Ejemplos de `/healthz` y `/readyz`.
- Resultado de `pytest -q`.
- Si se publica en nube, URL del servicio, revisión desplegada, configuración de autenticación y pruebas protegidas.

### Resultado de pruebas automatizadas del paquete

En el entorno de preparación del repositorio se ejecutó `pytest -q`: **11 pruebas aprobadas**. Incluyen liveness, readiness con predictor simulado, contrato de predicción, ausencia de modelo, validación de entradas, frontend y metadata. Estas pruebas no ejecutan Sentence Transformers ni el `.joblib` real, que se exporta posteriormente desde Drive.

