# Validación y pruebas del asistente inteligente de tickets

## 1. Objetivo

Documentar las pruebas realizadas sobre la versión contenerizada del asistente, sus validaciones de entrada, la API y la integración continua. Se separan los resultados efectivamente observados de los escenarios pendientes o propuestos.

## 2. Entorno y artefactos validados

- Imagen Docker: `asistente-tickets:1.0.0`.
- Contenedor local: `asistente-tickets`.
- Puerto publicado: `8080:8080`.
- Backend: FastAPI con Uvicorn.
- Encoder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Clasificador: Logistic Regression.
- Umbral configurado: `0.50`.
- Dataset de referencia: BANKING77 traducido al español (benchmark académico).

La imagen se construyó en Windows mediante Docker Desktop con el comando:

```powershell
docker build --build-arg PRELOAD_ENCODER=true -t asistente-tickets:1.0.0 .
```

Resultado observado: `Building 175.5s (16/16) FINISHED`, imagen etiquetada como `asistente-tickets:1.0.0`. La capa de precarga del encoder terminó satisfactoriamente.

El contenedor se inició y apareció con estado `Up` y `healthy`, con el puerto local 8080 conectado al puerto 8080 del contenedor.

## 3. Pruebas de inicialización y disponibilidad

Los registros del contenedor mostraron:

- `Loading weights: 100% | 199/199`.
- `Pipeline de clasificación cargado correctamente.`
- `Application startup complete.`
- `Uvicorn running on http://0.0.0.0:8080`.
- Respuestas HTTP 200 de `/healthz` y `/readyz`.
- Respuestas HTTP 200 al cargar la interfaz, archivos estáticos y documentación `/docs`.

Estos registros demuestran que la aplicación y el pipeline se inicializaron en Docker. No equivalen a una prueba de carga o de disponibilidad productiva.

## 4. Pruebas funcionales de clasificación

### 4.1 Transferencia no recibida

Entrada:

> No he recibido una transferencia que me hicieron en la mañana

Resultado observado en interfaz y API:

| Campo | Resultado |
|---|---|
| HTTP | 200 en la API |
| `model_name` | `logistic_regression` |
| `predicted_intent` | `transfer_not_received_by_recipient` |
| `predicted_intent_id` | 66 |
| `confidence` | aproximadamente 0.3332 (33.3%) |
| `confidence_threshold` | 0.50 |
| `decision` | `human_review` |
| `requires_human_review` | `true` |
| `priority_assigned` | `null` |

Evaluación: la intención corresponde semánticamente al texto, pero su puntuación queda debajo del umbral configurado y el sistema solicita revisión humana.

### 4.2 Tarjeta perdida

Entrada:

> Quiero congelar temporalmente mi tarjeta porque la perdí.

Resultado observado en interfaz y API:

| Campo | Resultado |
|---|---|
| HTTP | 200 en la API |
| `predicted_intent` | `lost_or_stolen_card` |
| `predicted_intent_id` | 41 |
| `confidence` | aproximadamente 0.809 (80.9%) |
| `confidence_threshold` | 0.50 |
| `decision` | `suggestion` |
| `requires_human_review` | `false` |
| `priority_assigned` | `null` |

Evaluación: el modelo presenta una sugerencia por encima del umbral. La sugerencia debe ser confirmada por el agente; no ejecuta una operación bancaria ni asigna prioridad.

### 4.3 Consulta fuera del dominio (OOD)

Entrada:

> Hola, ¿me pueden decir cuál es el horario de atención?

Resultado observado en interfaz:

| Campo | Resultado |
|---|---|
| `predicted_intent` | `card_delivery_estimate` |
| `predicted_intent_id` | 12 |
| `confidence` | 82.3% |
| Decisión | Sugerencia para confirmación del agente |

Evaluación: clasificación incorrecta para una consulta que no corresponde claramente a las intenciones del benchmark. Este caso muestra que el clasificador cerrado fuerza una de las 77 etiquetas y que un umbral de 0.50 no es un detector de consultas fuera del dominio. Se identifica como mejora futura evaluar detección OOD, rechazo/derivación y ejemplos de consultas fuera del dominio.

**No se debe concluir que un porcentaje alto garantiza corrección.** Las puntuaciones no están calibradas y el caso anterior ilustra este riesgo.

## 5. Pruebas de validación de entradas

### 5.1 Interfaz web

Se observaron mensajes de validación del navegador para:

- Campo vacío: `Completa este campo`.
- Texto de un carácter: `Aumenta la longitud de este texto a 3 caracteres o más`.

Estas pruebas demuestran la validación del lado del navegador.

### 5.2 API directa mediante Swagger UI

Endpoint probado: `POST /api/predict`.

| Caso | Request body | Respuesta observada | Evaluación |
|---|---|---|---|
| Campo obligatorio ausente | `{}` | HTTP 422; `loc: ["body", "text"]`; `msg: "Field required"` | Correcto |
| Texto menor al mínimo | `{"text":"a"}` | HTTP 422; `type: "string_too_short"`; mínimo 3 caracteres | Correcto |
| Solicitud válida: transferencia | Texto de transferencia no recibida | HTTP 200 y JSON de predicción | Correcto |
| Solicitud válida: tarjeta perdida | Texto de tarjeta perdida | HTTP 200 y JSON de predicción | Correcto |

Las respuestas 422 son resultados esperados de la validación de entrada; no representan fallas de la aplicación.

## 6. Pruebas de registros y errores no bloqueantes

En los registros apareció una consulta HTTP 404 de Hugging Face al recurso opcional `additional_chat_templates`. Después se consultaron recursos disponibles con HTTP 200 y el pipeline se cargó correctamente. No impidió el arranque.

También apareció `GET /favicon.ico` con HTTP 404 porque no se incluyó un favicon. Es un recurso visual opcional y no afectó a los endpoints de la API.

En los registros revisados, las peticiones de `/healthz`, `/readyz`, `/docs` y las inferencias válidas respondieron con HTTP 200; las solicitudes inválidas devolvieron HTTP 422 conforme a lo esperado.

## 7. Integración continua con GitHub Actions

Repositorio: `https://github.com/AlexAguilarG/asistente-tickets-bancarios`

Workflow: `.github/workflows/tests.yml`.

Durante la primera ejecución se identificaron dos problemas de configuración del entorno:

1. Python no encontraba el paquete local `app`; se incorporó `PYTHONPATH: ${{ github.workspace }}` y ejecución mediante `python -m pytest`.
2. El entorno de CI no instalaba dependencias de ejecución del predictor, por lo que faltaba `joblib`; el workflow se ajustó para instalar `requirements-runtime.lock` y después `requirements-dev.txt`.

La captura de GitHub correspondiente al commit `1d9ecf3` mostró la ejecución `api-tests` exitosa, con `1/1` trabajo completado. Las ejecuciones rojas anteriores corresponden a commits previos y no deben confundirse con el último estado validado.

## 8. Matriz resumida de resultados

| ID | Escenario | Resultado observado | Estado |
|---|---|---|---|
| T01 | Construcción de imagen Docker | 16/16 pasos completados | PASS |
| T02 | Arranque del contenedor | Estado `healthy` | PASS |
| T03 | Endpoint `/healthz` | HTTP 200 | PASS |
| T04 | Endpoint `/readyz` | HTTP 200 | PASS |
| T05 | Interfaz y documentación Swagger | HTTP 200 | PASS |
| T06 | Campo vacío en interfaz | Navegador bloquea envío | PASS |
| T07 | Texto de 1 carácter en interfaz | Navegador exige mínimo 3 | PASS |
| T08 | API sin `text` | HTTP 422 | PASS |
| T09 | API con texto de 1 carácter | HTTP 422 | PASS |
| T10 | Inferencia de transferencia | HTTP 200; revisión humana | PASS funcional |
| T11 | Inferencia de tarjeta perdida | HTTP 200; sugerencia | PASS funcional |
| T12 | Consulta de horario fuera del dominio | Etiqueta incorrecta con 82.3% | HALLAZGO / LIMITACIÓN |
| T13 | GitHub Actions, commit `1d9ecf3` | `api-tests`, 1/1 trabajo exitoso | PASS |

`PASS funcional` significa que la API respondió y produjo la salida prevista por el flujo; no equivale a demostrar exactitud general del modelo ni aptitud productiva.

## 9. Limitaciones y trabajo pendiente

- No se desplegó la solución en Google Cloud Run. La nube se documenta como procedimiento propuesto en `MANUAL_DESPLIEGUE_NUBE.md`.
- No se ejecutaron pruebas de carga, estrés, latencia bajo concurrencia ni tolerancia a fallos.
- No se probó con tickets reales de una institución bancaria mexicana.
- BANKING77 traducido es un benchmark y no debe presentarse como muestra representativa de clientes mexicanos.
- No se calibraron las puntuaciones; el umbral 0.50 es una configuración exploratoria, no una política aprobada.
- No se implementó detección OOD específica.
- No hay modelo ni reglas operativas aprobadas para priorización automática.
- La sugerencia con `requires_human_review=false` sigue requiriendo confirmación del agente, de acuerdo con el alcance del prototipo.
- No se ha aprobado la solución para producción.

## 10. Conclusión

La validación demuestra que la aplicación se puede construir y ejecutar localmente en Docker, que FastAPI carga el encoder y el clasificador, que la API procesa solicitudes válidas, que rechaza entradas que incumplen el esquema y que GitHub Actions finalizó correctamente en el último commit verificado. También se detectó un fallo de clasificación fuera del dominio, que se documenta como limitación y mejora requerida. Los resultados respaldan un prototipo académico funcional, no una solución lista para producción.
