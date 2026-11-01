# Arquitectura técnica del asistente

## 1. Objetivo y alcance

Exponer como aplicación web el pipeline ya evaluado en las actividades anteriores para sugerir una intención de una consulta de banca digital. Se conserva el encoder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` y el clasificador de Regresión Logística de 77 clases. No se entrena un modelo nuevo.

**Fuera de alcance de esta versión:** asignación automática de prioridad, conexión con sistemas bancarios, consulta de cuentas, ejecución de pagos/transferencias, autenticación de clientes y uso con datos reales. La prioridad queda sin asignar (`null`) porque no existe un modelo o matriz de reglas de prioridad validada en los artefactos compartidos.

## 2. Componentes

| Componente | Responsabilidad | Tecnología |
|---|---|---|
| Frontend | Capturar un texto ficticio y mostrar la sugerencia, confianza y necesidad de revisión | HTML, CSS, JavaScript |
| API / backend | Validar solicitudes, ejecutar el pipeline y devolver JSON | FastAPI + Uvicorn |
| Encoder | Convertir el texto en un embedding normalizado | Sentence Transformers / MiniLM |
| Clasificador | Elegir una de las 77 intenciones y devolver probabilidades | scikit-learn / Regresión Logística |
| Artefactos | Clasificador, catálogo de intenciones y manifiesto de versiones | joblib + JSON |
| Contenedor | Empaquetar sistema, dependencias y configuración | Docker |
| Nube propuesta | Ejecutar la imagen como servicio administrado | Google Cloud Run (PaaS/serverless de contenedores) |

## 3. Flujo de inferencia

1. El usuario escribe un mensaje ficticio en el frontend.
2. El frontend envía `POST /api/predict` con `{ "text": "..." }`.
3. FastAPI valida que el texto no esté vacío y que no supere 5,000 caracteres.
4. MiniLM genera un embedding con `normalize_embeddings=True`, como en el pipeline evaluado.
5. Regresión Logística devuelve `predict_proba`; se toma la clase de mayor probabilidad.
6. Se compara la probabilidad máxima con el umbral configurado (0.50 por defecto, solo candidato exploratorio).
7. La API devuelve la intención sugerida y un indicador de revisión humana. No asigna prioridad.

## 4. Contrato de API

### `GET /healthz`

Liveness del proceso. Devuelve `200` si el servidor responde, aunque el modelo todavía no se haya cargado.

### `GET /readyz`

Readiness del pipeline. Devuelve `200` cuando el clasificador y el encoder están cargados; de lo contrario `503`.

### `GET /api/metadata`

Devuelve nombre del modelo, encoder, número de intenciones, umbral configurado y alcance funcional.

### `POST /api/predict`

Solicitud:

```json
{ "text": "Mi transferencia no llegó al destinatario" }
```

Respuesta ilustrativa de estructura (los valores se generan en tiempo de ejecución y no son una predicción garantizada):

```json
{
  "model_name": "logistic_regression",
  "predicted_intent_id": 66,
  "predicted_intent": "transfer_not_received_by_recipient",
  "confidence": 0.82,
  "confidence_threshold": 0.5,
  "decision": "suggestion",
  "requires_human_review": false,
  "priority_assigned": null,
  "priority_note": "La prioridad debe establecerse mediante reglas aprobadas por Operación.",
  "disclaimer": "Prototipo académico; no producción bancaria."
}
```

La respuesta es un ejemplo del contrato, no un resultado medido de la aplicación.

## 5. Dependencias y portabilidad

El notebook de exportación crea `models/model_manifest.json` y `requirements-runtime.lock` desde las versiones del entorno de Colab. Docker utiliza el lock si está presente y, en caso contrario, usa `requirements.txt`. Para reproducir el artefacto serializado se recomienda usar el lock generado junto con Python 3.13, que coincide con el runtime de Colab observado durante la Actividad 6.

El encoder no está incluido dentro del archivo joblib. Se descarga desde Hugging Face al iniciar el servicio y se almacena en `HF_HOME`; la primera inicialización requiere conexión a internet y puede tardar. La revisión (commit) del encoder se fija en el manifiesto si Colab puede consultar Hugging Face al exportar.

## 6. Seguridad y límites

- No registrar ni persistir el texto del ticket en logs o bases de datos.
- En esta versión se recomienda usar únicamente datos sintéticos.
- No se incluye autenticación de usuario final; no exponer públicamente para uso con información bancaria.
- Usar TLS, autenticación IAM/OIDC, autorización, gestión de secretos, límites de tasa, monitoreo y controles de red antes de un piloto institucional.
- Cargar exclusivamente el `.joblib` generado por el propio proyecto; pickle/joblib no es seguro frente a artefactos no confiables.
- El score máximo no equivale a una probabilidad calibrada. El umbral 0.50 no está aprobado para producción.

## 7. Alineación documental con ISO/IEC 23053

La documentación organiza el sistema en términos de propósito, datos de entrada, componentes, modelo ML, interfaz, inferencia, límites, despliegue, monitoreo y gobernanza. Es una **alineación documental orientativa**, no una certificación ni una declaración de conformidad formal con ISO/IEC 23053:2022.
