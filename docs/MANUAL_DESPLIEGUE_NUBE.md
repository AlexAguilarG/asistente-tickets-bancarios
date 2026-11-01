# Manual de despliegue en la nube

## 1. Propósito y alcance

Este manual describe un procedimiento reproducible para desplegar el **Asistente de tickets bancarios** en Google Cloud Run a partir de la imagen Docker del proyecto. La estrategia combina contenedores con un servicio administrado tipo PaaS.

**Estado de implementación:** este despliegue en la nube es una propuesta técnica documentada; no se ejecutó ni se crearon recursos de Google Cloud para esta actividad. La aplicación sí fue construida y ejecutada localmente en Docker, y su API fue probada. Por tanto, los comandos de este documento son instrucciones de referencia y no evidencias de una publicación cloud completada.

La solución clasifica el texto de un ticket en una de 77 intenciones. No asigna prioridad automáticamente ni sustituye la revisión humana. El modelo se entrenó/evaluó con BANKING77 traducido; este benchmark no representa tickets reales de un banco mexicano. Las puntuaciones de confianza no están calibradas para uso productivo.

## 2. Estrategia de despliegue

Se propone un flujo **PaaS + contenedores**:

1. **GitHub:** conserva el código fuente, el Dockerfile, la configuración y las pruebas.
2. **Cloud Build:** construye la imagen del contenedor desde el repositorio de trabajo.
3. **Artifact Registry:** almacena la imagen versionada.
4. **Cloud Run:** ejecuta el contenedor como un servicio administrado y expone HTTPS.
5. **Cloud Logging y Cloud Monitoring:** permiten consultar registros, errores, disponibilidad y consumo.

La imagen incluye FastAPI, Sentence Transformers, el encoder multilingüe `paraphrase-multilingual-MiniLM-L12-v2`, el clasificador de regresión logística y los archivos de etiquetas/manifiesto. El Dockerfile utiliza `PRELOAD_ENCODER=true` durante la construcción para precargar el encoder en la imagen, siguiendo la construcción local que ya se verificó.

### Región propuesta

Se propone `northamerica-south1` (México), región disponible para Cloud Run y Artifact Registry. La ubicación definitiva debe considerar latencia, residencia de datos, disponibilidad regional y ubicación de los demás servicios. La disponibilidad y el nivel de precios deben verificarse nuevamente al momento de una implementación real.

## 3. Requerimientos técnicos

### 3.1 Cuenta y proyecto

- Cuenta de Google Cloud con acceso a un proyecto.
- Proyecto con facturación vinculada y activa para habilitar y utilizar los servicios facturables.
- Permisos para habilitar APIs, crear repositorios, ejecutar builds, desplegar servicios y configurar IAM.
- Google Cloud CLI (`gcloud`) instalado y autenticado.
- Acceso al repositorio GitHub y a la carpeta raíz del proyecto.

### 3.2 Servicios y APIs

Se requieren, como mínimo, Cloud Build, Cloud Run, Artifact Registry y Service Usage. Resource Manager puede ser requerido para operaciones de proyecto. Las APIs se habilitan explícitamente en el procedimiento.

### 3.3 Artefactos del proyecto

- `Dockerfile` y `.dockerignore`.
- `cloudbuild.yaml`.
- `app/` con FastAPI, predictor, esquemas e interfaz estática.
- `models/logistic_regression_classifier.joblib`.
- `models/intent_labels.json` y `models/model_manifest.json`.
- `requirements-runtime.lock` y `requirements.txt`.

El encoder se descarga/precarga durante la construcción de la imagen por el argumento `PRELOAD_ENCODER=true`. La disponibilidad de red hacia Hugging Face durante Cloud Build es un prerrequisito de esa estrategia.

### 3.4 Identidades y permisos

Se deben aplicar permisos de mínimo privilegio y confirmar qué cuenta de servicio utiliza Cloud Build en el proyecto concreto. No se debe asumir que todos los proyectos utilizan la misma cuenta de servicio predeterminada.

Como referencia, la cuenta de servicio de Cloud Build puede requerir permisos para escribir en Artifact Registry, desplegar en Cloud Run, escribir registros y actuar sobre la cuenta de servicio de ejecución de Cloud Run. La documentación de Google Cloud describe roles como Artifact Registry Writer, Cloud Run Admin, Logs Writer y Service Account User, además de los permisos de Cloud Build que correspondan. La persona que despliega también necesita permisos para crear el repositorio y habilitar APIs. Los roles exactos deben revisarse en **Cloud Build > Settings / Permissions** y en la configuración IAM del proyecto antes de concederlos.

La cuenta de servicio de ejecución de Cloud Run debe tener únicamente los permisos que requiera la aplicación. En la versión actual, el modelo y el encoder están dentro de la imagen; no se documenta acceso de ejecución a datos de clientes ni a almacenamiento externo.

## 4. Procedimiento de despliegue propuesto

Los comandos siguientes son ejemplos para PowerShell. Sustituir `REEMPLAZAR_CON_PROJECT_ID` por el identificador real del proyecto. **No ejecutar este procedimiento si no se cuenta con autorización y presupuesto.**

### Paso 1. Autenticar y seleccionar el proyecto

```powershell
$PROJECT_ID = "REEMPLAZAR_CON_PROJECT_ID"
$REGION = "northamerica-south1"
$SERVICE = "asistente-tickets"
$REPOSITORY = "asistente-tickets"
$IMAGE = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/api:v1.0.0"

gcloud auth login
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
gcloud config get-value project
```

Verificar que el proyecto seleccionado sea el correcto antes de continuar.

### Paso 2. Habilitar las APIs necesarias

```powershell
gcloud services enable `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  run.googleapis.com `
  serviceusage.googleapis.com `
  cloudresourcemanager.googleapis.com
```

Habilitar APIs puede requerir permisos de Service Usage Admin o permisos equivalentes. La habilitación y el uso de servicios puede tener implicaciones de facturación.

### Paso 3. Crear el repositorio de Artifact Registry

```powershell
gcloud artifacts repositories create $REPOSITORY `
  --repository-format=docker `
  --location=$REGION `
  --description="Imagen del asistente de clasificación de tickets"
```

El repositorio debe existir antes de enviar la imagen. Si ya existe, verificar que sea de formato Docker y que corresponda a la misma región utilizada en la URL de la imagen.

### Paso 4. Revisar permisos de Cloud Build

En Google Cloud Console, revisar la cuenta de servicio configurada para Cloud Build y otorgar únicamente los roles necesarios para:

- Construir la imagen.
- Subirla a Artifact Registry.
- Desplegar el servicio en Cloud Run.
- Escribir registros de compilación.
- Suplantar la cuenta de servicio de ejecución de Cloud Run, cuando aplique.

La asignación concreta depende de la cuenta de servicio configurada y de las políticas del proyecto. No utilizar el rol Owner como solución general ni copiar un correo de cuenta de servicio de otro proyecto.

### Paso 5. Construir, publicar y desplegar con Cloud Build

El archivo `cloudbuild.yaml` del repositorio define tres pasos: construir la imagen, subirla a Artifact Registry y desplegarla en Cloud Run. La imagen se construye con `PRELOAD_ENCODER=true`, el mismo mecanismo utilizado en la validación local.

```powershell
$SUBSTITUTIONS = "_REGION=$REGION,_SERVICE=$SERVICE,_IMAGE=$IMAGE"
gcloud builds submit `
  --config=cloudbuild.yaml `
  --substitutions=$SUBSTITUTIONS `
  .
```

Cloud Build ejecutará los pasos y mostrará el estado de la compilación. Una compilación exitosa no sustituye las pruebas funcionales posteriores.

### Paso 6. Configuración del servicio

La configuración de referencia del archivo `cloudbuild.yaml` mantiene:

- Puerto de escucha: `8080`.
- Umbral de clasificación: `CONFIDENCE_THRESHOLD=0.50`.
- Dispositivo del modelo: `MODEL_DEVICE=cpu`.
- Telemetría de Hugging Face deshabilitada: `HF_HUB_DISABLE_TELEMETRY=1`.
- Acceso sin autenticación deshabilitado (`--no-allow-unauthenticated`).
- Límite inicial propuesto de 2 instancias y mínimo 0.
- Configuración inicial propuesta de 2 vCPU, 2 GiB de memoria y concurrencia 5.

CPU, memoria, concurrencia y límite de instancias son **parámetros iniciales propuestos, no valores medidos en Cloud Run**. Deben ajustarse después de medir consumo de memoria, latencia de arranque, tiempo de inferencia y concurrencia con cargas representativas. El límite de instancias reduce el crecimiento accidental, pero no constituye por sí mismo un presupuesto máximo de facturación.

### Paso 7. Consultar URL y estado del servicio

```powershell
gcloud run services describe $SERVICE `
  --region=$REGION `
  --format="value(status.url)"

gcloud run services describe $SERVICE `
  --region=$REGION `
  --format="yaml(status.conditions)"
```

La URL devuelta identifica el servicio. Como el despliegue se configuró privado, una solicitud anónima no debe considerarse una prueba válida de la API.

### Paso 8. Probar un servicio privado

Google Cloud CLI permite crear un proxy local autenticado. En una terminal de PowerShell:

```powershell
gcloud run services proxy $SERVICE --project=$PROJECT_ID --region=$REGION --port=8080
```

Mientras el proxy permanezca activo, utilizar otra terminal para comprobar:

```powershell
Invoke-RestMethod http://localhost:8080/healthz
Invoke-RestMethod http://localhost:8080/readyz
```

También se puede abrir `http://localhost:8080/docs` para consultar la documentación interactiva de FastAPI. El acceso se realiza a través del proxy autenticado; no se debe habilitar acceso público únicamente para facilitar una demostración.

Para probar una predicción:

```powershell
$body = @{ text = "No he recibido una transferencia que me hicieron en la mañana" } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/api/predict `
  -ContentType "application/json" `
  -Body $body
```

### Paso 9. Consultar registros

```powershell
gcloud run services logs read $SERVICE --region=$REGION --limit=50
```

Revisar el arranque del pipeline, errores de carga del encoder, solicitudes HTTP, latencia y errores de aplicación. No registrar texto bancario real ni datos personales en logs.

## 5. Validación posterior al despliegue

Una implementación real debería repetir al menos las pruebas siguientes:

| Caso | Entrada / acción | Resultado esperado |
|---|---|---|
| Salud | `GET /healthz` | HTTP 200 |
| Disponibilidad | `GET /readyz` | HTTP 200 cuando el pipeline está listo |
| API sin `text` | `{}` | HTTP 422 |
| Texto corto | `{"text":"a"}` | HTTP 422 |
| Ticket válido | Transferencia no recibida | HTTP 200 y respuesta estructurada |
| Otra intención | Tarjeta perdida | HTTP 200 y respuesta estructurada |
| Consulta fuera del dominio | Pregunta de horario | Evaluar rechazo/OOD; no aceptar automáticamente una intención forzada |

Los resultados locales que respaldan el diseño están en `VALIDACION_Y_PRUEBAS.md`. No se deben copiar dichos resultados como si fueran pruebas ejecutadas en Cloud Run.

## 6. Seguridad y límites operativos

- Mantener el servicio privado con autenticación IAM mientras no exista una arquitectura de acceso público formalmente aprobada.
- No introducir datos reales de clientes en el benchmark, pruebas, prompts, capturas ni logs.
- No almacenar secretos en GitHub, Dockerfile, `cloudbuild.yaml` o variables versionadas. Para secretos futuros, utilizar Secret Manager y referencias de secretos en Cloud Run.
- Aplicar mínimo privilegio a cuentas de usuario, Cloud Build y Cloud Run.
- La interfaz de clasificación es una ayuda al agente. No autoriza transferencias, bloqueos de tarjetas ni decisiones operativas.
- Agregar evaluación OOD antes de aceptar automáticamente entradas que no correspondan a las 77 intenciones.
- Calibrar las puntuaciones y validar umbrales con tickets representativos antes de cualquier uso productivo.
- Medir memoria/CPU y latencia con concurrencia controlada. El encoder y PyTorch hacen que el contenedor sea más pesado que una API convencional.

## 7. Costos y control presupuestario

El procedimiento no se ejecutó porque el alcance académico se limita a documentar la estrategia cloud y no se cuenta con presupuesto autorizado para activar los servicios. La cuenta de Google Cloud por sí sola no demuestra que la facturación esté habilitada ni que exista presupuesto disponible.

Una ejecución real puede generar cargos por:

- Tiempo de compilación en Cloud Build.
- Almacenamiento de la imagen en Artifact Registry y transferencia de datos.
- CPU, memoria, solicitudes y transferencia de salida de Cloud Run.
- Cloud Logging, Monitoring y otros servicios auxiliares.

Cloud Run tiene un modelo de consumo y cuotas gratuitas sujetas a condiciones; Cloud Build y Artifact Registry tienen reglas de cobro independientes. No se presenta un costo estimado porque dependería de región, tamaño final de imagen, número/duración de builds, tráfico, memoria/CPU, retención y logs. Antes de ejecutar, debe utilizarse la calculadora oficial y configurar presupuestos/alertas. Una alerta presupuestaria notifica; no debe asumirse que detiene automáticamente el consumo.

## 8. Herramientas de documentación y referencia ISO/IEC 23053

Se utilizó ChatGPT como apoyo generativo para organizar, redactar y revisar instrucciones técnicas y para explicar errores del proceso de desarrollo. GitHub Actions, Docker, FastAPI y Swagger aportaron evidencia técnica de construcción, pruebas e interfaz de API.

El repositorio incluye `docs/USO_COPILOT.md` con un prompt y una guía para utilizar GitHub Copilot como apoyo complementario. **No se afirma que GitHub Copilot haya sido ejecutado en este proyecto.** Si se utiliza posteriormente, se debe conservar el prompt, fecha, propuesta generada y correcciones realizadas por el responsable.

La estructura de documentación toma ISO/IEC 23053:2022 como referencia conceptual para describir propósito, componentes, datos, modelo, entorno, evaluación, operación, riesgos y límites. Esto no constituye certificación ni declaración de conformidad con la norma.

## 9. Conclusión

La solución tiene una imagen Docker construida y ejecutada localmente, API funcional, pruebas manuales documentadas y un repositorio GitHub con integración continua. El despliegue en Google Cloud Run queda especificado como procedimiento reproducible, pero **no fue realizado**. Para una futura implementación se requieren proyecto con facturación, permisos IAM, configuración de recursos, pruebas de carga y validación con datos representativos y autorizados.

## 10. Documentación oficial

- Cloud Build: desplegar en Cloud Run: https://docs.cloud.google.com/build/docs/deploying-builds/deploy-cloud-run
- Cloud Run: ubicaciones: https://docs.cloud.google.com/run/docs/locations
- Artifact Registry: desplegar en Cloud Run: https://docs.cloud.google.com/artifact-registry/docs/integrate-cloud-run
- Cloud Run: solicitudes HTTPS y servicios privados: https://docs.cloud.google.com/run/docs/triggering/https-request
- `gcloud run services proxy`: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/proxy
- Cloud Run pricing: https://cloud.google.com/run/pricing
- Artifact Registry pricing: https://cloud.google.com/artifact-registry/pricing
