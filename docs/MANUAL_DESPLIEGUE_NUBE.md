# Manual de despliegue en la nube (propuesta PaaS con Google Cloud Run)

## 1. Decisión de arquitectura

Se propone **Google Cloud Run** como servicio administrado para ejecutar la misma imagen Docker validada localmente. Cloud Run es adecuado para una demostración PaaS/serverless basada en contenedores: recibe una imagen, administra instancias y requiere que el proceso escuche en el puerto indicado por la variable `PORT` que inyecta la plataforma.

La alternativa está documentada, pero **no se ha desplegado todavía**. El despliegue real requiere una cuenta/proyecto de Google Cloud, permisos IAM, configuración de facturación y autorización de la organización si se utilizará información institucional.

## 2. Requisitos

- Proyecto de Google Cloud con facturación habilitada.
- Google Cloud CLI (`gcloud`) instalado y autenticado.
- APIs: Cloud Run, Artifact Registry y Cloud Build.
- Imagen construida a partir del Dockerfile y artefacto de modelo propio.
- Región permitida por las políticas de residencia de datos y latencia del proyecto.
- Permisos para crear repositorios de Artifact Registry, ejecutar Cloud Build y desplegar servicios Cloud Run.

## 3. Preparar el proyecto

Inicia sesión y selecciona el proyecto:

```bash
gcloud auth login
gcloud config set project PROJECT_ID
```

Habilita los servicios:

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

Define variables (sustituir los valores entre `< >`):

```bash
PROJECT_ID="<ID_DEL_PROYECTO>"
REGION="<REGION_APROBADA>"
REPOSITORY="asistente-tickets"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/api:1.0.0"
SERVICE="asistente-tickets"
```

Crea el repositorio Docker en Artifact Registry:

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Imagen del asistente de clasificación de tickets"
```

## 4. Construir y publicar la imagen

Desde la raíz del proyecto, con `Dockerfile`, `models/` y `requirements-runtime.lock`:

```bash
gcloud builds submit --timeout=1800s --tag "$IMAGE"
```

Cloud Build ejecuta el Dockerfile y publica la imagen en Artifact Registry. La documentación oficial de Google describe el flujo `gcloud builds submit --tag IMAGE_URL` para crear la imagen desde las fuentes y el Dockerfile. El Dockerfile descarga MiniLM durante la construcción de la imagen; esto aumenta el tamaño/tiempo de build, pero evita depender de una descarga de Hugging Face al iniciar cada instancia.

## 5. Desplegar en Cloud Run

Para un entorno institucional se recomienda exigir autenticación (no permitir invocación pública):

```bash
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --port 8080 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --min 0 \
  --max 3 \
  --no-allow-unauthenticated \
  --set-env-vars CONFIDENCE_THRESHOLD=0.50,MODEL_DEVICE=cpu,HF_HUB_DISABLE_TELEMETRY=1
```

Los recursos (`4Gi`, `2 CPU`, concurrencia, mínimos/máximos) son punto de partida para prueba académica, no dimensionamiento productivo. Se deben medir uso de RAM/CPU, tiempo de carga del encoder, latencia p50/p95, solicitudes concurrentes y costo.

Para permitir invocación desde un frontend autenticado, asigna `roles/run.invoker` únicamente a identidades/grupos aprobados. En una demostración con textos exclusivamente sintéticos puede habilitarse temporalmente `--allow-unauthenticated`, siempre documentando que no es configuración bancaria.

## 6. Obtener URL y probar

```bash
gcloud run services describe "$SERVICE" \
  --region "$REGION" \
  --format='value(status.url)'
```

Para un servicio privado, prueba con un token de identidad de una cuenta autorizada:

```bash
SERVICE_URL="<URL_DEVUELTA_POR_EL_COMANDO>"
TOKEN="$(gcloud auth print-identity-token)"
curl -H "Authorization: Bearer ${TOKEN}" "${SERVICE_URL}/healthz"
curl -H "Authorization: Bearer ${TOKEN}" "${SERVICE_URL}/readyz"
curl -X POST "${SERVICE_URL}/api/predict" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Mi transferencia no llegó al destinatario"}'
```

Verifica además la interfaz web en la URL base y la documentación `/docs` si el acceso está permitido por IAM.

## 7. Operación, seguridad y monitoreo

Antes de cualquier piloto bancario:

- Mantener la API privada y protegerla con IAM/OIDC o el mecanismo corporativo aprobado.
- No permitir datos reales hasta recibir autorización formal, definir base legal, controles de privacidad y proceso de anonimización.
- Revisar la política de residencia de datos, retención, logs y acceso de operadores.
- Configurar límites de instancias, CPU/memoria, timeout y concurrencia tras pruebas de carga.
- Revisar Cloud Logging y métricas de Cloud Monitoring; no escribir el contenido íntegro del ticket en logs.
- Mantener versiones inmutables de imágenes y un proceso de rollback.
- Monitorear latencia, errores HTTP, disponibilidad, tasa de revisión humana, cambios de distribución y calidad por intención.
- Calibrar las probabilidades y volver a seleccionar el umbral con datos de validación antes de cualquier automatización.

La caché de Hugging Face se incluye en la imagen al construirla. Si se cambia el encoder o su revisión, es necesario reconstruir y volver a publicar la imagen.

La puntuación máxima de Regresión Logística no es una probabilidad calibrada. El 0.50 es el umbral exploratorio inicial y no debe tratarse como una aprobación productiva.

## 8. Alternativas de despliegue

| Opción | Característica | Cuándo considerarla |
|---|---|---|
| Cloud Run (propuesta) | PaaS/serverless para contenedores, escalado administrado | Demostración, API HTTP y demanda variable |
| Kubernetes gestionado | Mayor control sobre orquestación y topología | Cuando existan varios servicios, redes complejas o requerimientos avanzados |
| Nube privada / híbrida | Control organizacional sobre redes y datos sensibles | Cuando políticas, residencia o integración bancaria lo exijan |

La decisión final debe evaluarse con Seguridad, Arquitectura, Riesgo, Operación y Cumplimiento. El Tema 16 distingue los modelos de implementación (pública, privada, híbrida y multinube) de los modelos de servicio (IaaS, PaaS, SaaS y FaaS); esta propuesta selecciona PaaS para el ejercicio demostrativo, sin afirmar que sea automáticamente la opción productiva del banco.

## 9. Referencias de implementación

- Google Cloud. *Build sources to containers*. https://docs.cloud.google.com/run/docs/building/containers
- Google Cloud. *Deploy container images to Cloud Run services*. https://docs.cloud.google.com/run/docs/deploying
- Google Cloud. *Configure Cloud Run services*. https://docs.cloud.google.com/run/docs/configuring
- Google Cloud. *Configure container health checks for services*. https://docs.cloud.google.com/run/docs/configuring/healthchecks
