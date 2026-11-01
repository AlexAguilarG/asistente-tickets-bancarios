# Asistente inteligente para clasificación de tickets bancarios

**Actividad 7 (despliegue local y en la nube) — prototipo académico**

Esta aplicación expone mediante una API y una interfaz web el pipeline existente de la Actividad 5/6: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` + Regresión Logística para clasificar texto en 77 intenciones de BANKING77 traducido.

> **Alcance:** demostrador académico. No se conecta a sistemas bancarios, no procesa transacciones, no asigna prioridad y no debe recibir información real de clientes. El corpus BANKING77 traducido no ha demostrado representar el español financiero de un banco mexicano.

## Qué contiene

- API FastAPI: `/api/predict`, `/api/metadata`, `/healthz`, `/readyz` y Swagger `/docs`.
- Frontend web HTML/CSS/JavaScript servido por el mismo backend.
- Dockerfile, Docker Compose y Cloud Build para Cloud Run.
- Pruebas automatizadas del contrato HTTP.
- Manual local Docker, manual de despliegue PaaS y documento de pruebas.
- Notebook Colab para exportar el artefacto real desde Google Drive sin volver a entrenar.

## Estado del artefacto del modelo

El ZIP de código inicial no contiene el clasificador `.joblib`, porque ese archivo no se encontraba entre los materiales adjuntos. Para preparar la imagen, ejecuta `notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb`. El notebook busca `Actividad5/modelos/logistic_regression_classifier.joblib` en Drive, lo copia a `models/`, genera `model_manifest.json` y fija dependencias en `requirements-runtime.lock`. **No entrena ni ejecuta GridSearch.**

El encoder MiniLM se descarga de Hugging Face durante el build Docker y queda almacenado en la imagen; el primer build requiere internet y puede tardar, pero reduce la dependencia de red al iniciar el contenedor. La revisión del modelo se registra en el manifiesto cuando Colab puede consultar Hugging Face.

## Arquitectura

```text
Navegador
  └── Frontend HTML/CSS/JS
       └── POST /api/predict
            └── FastAPI
                 ├── SentenceTransformer MiniLM (embedding normalizado)
                 └── LogisticRegression (77 clases)
                      └── intención sugerida + score + revisión humana
```

El score máximo no equivale a una probabilidad calibrada. `CONFIDENCE_THRESHOLD=0.50` es un valor candidato de demostración basado en el análisis offline anterior; no está calibrado ni aprobado para el banco. Si no alcanza el umbral, el API marca el ticket para revisión humana. La prioridad queda sin asignar porque no existe una regla/modelo de prioridad validado.

## Requisitos

- Google Colab para exportar el clasificador de Drive.
- Docker Desktop o Docker Engine para construir y ejecutar el contenedor.
- Python 3.13 recomendado para coincidir con el runtime de Colab usado en la Actividad 6.
- Conexión a internet durante la primera carga del encoder.

## 1. Exportar desde Colab

1. Sube y descomprime este paquete en `/content/Asistente_Tickets_Despliegue`.
2. Abre `notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb`.
3. Ejecuta las celdas en orden y autoriza el montaje de Drive.
4. Descarga `Asistente_Tickets_Despliegue_LISTO.zip`.
5. Usa esa versión del paquete para el despliegue local y GitHub.

Si el notebook no encuentra el `.joblib`, regresa al notebook de Actividad 6 y confirma que se guardó el modelo en `Actividad5/modelos/`. No ejecutes entrenamiento de nuevo si el artefacto ya existe.

## 2. Pruebas de API sin artefacto real

Estas pruebas utilizan un predictor simulado y validan contrato, códigos HTTP y casos de entrada; no prueban la exactitud del modelo.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## 3. Construir y ejecutar con Docker

Después de usar el ZIP LISTO de Colab:

```bash
python scripts/verify_artifacts.py
docker build --build-arg PRELOAD_ENCODER=true -t asistente-tickets:1.0.0 .
docker run --rm --name asistente-tickets -p 8080:8080 \
  -e CONFIDENCE_THRESHOLD=0.50 \
  -v tickets-hf-cache:/home/app/.cache/huggingface \
  asistente-tickets:1.0.0
```

O con Docker Compose:

```bash
docker compose up --build
```

Abre:

- Interfaz: http://localhost:8080/
- Swagger: http://localhost:8080/docs
- Liveness: http://localhost:8080/healthz
- Readiness: http://localhost:8080/readyz
- Metadata: http://localhost:8080/api/metadata

Prueba:

```bash
curl -X POST http://localhost:8080/api/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Mi transferencia no llegó al destinatario"}'
```

## 4. Despliegue en nube

La propuesta de este ejercicio es Google Cloud Run (PaaS de contenedores). Revisa `docs/MANUAL_DESPLIEGUE_NUBE.md`. El servicio debe permanecer privado para un escenario bancario; no uses datos reales en una demo pública. La documentación describe los pasos, pero no afirma que ya exista un servicio desplegado.

## 5. Documentación del proyecto

- `docs/ARQUITECTURA_TECNICA.md`
- `docs/MANUAL_DESPLIEGUE_LOCAL_DOCKER.md`
- `docs/MANUAL_DESPLIEGUE_NUBE.md`
- `docs/VALIDACION_Y_PRUEBAS.md`

## 6. GitHub

Crea un repositorio vacío (por ejemplo `asistente-tickets-bancarios`) y sube la carpeta del ZIP LISTO, que ya incluirá el artefacto propio y `requirements-runtime.lock`:

```bash
git init
git add .
git commit -m "feat: API, frontend y despliegue Docker del asistente de tickets"
git branch -M main
git remote add origin https://github.com/<USUARIO>/asistente-tickets-bancarios.git
git push -u origin main
```

No incluyas datos de clientes, `.env`, credenciales, `mlflow.db` ni tokens. El modelo joblib propio puede versionarse si el tamaño está dentro de los límites del repositorio y la política académica/institucional lo permite. Para modelos grandes, usar Git LFS o un registry privado.

## Referencias

- Material del curso, *Tema 15. Despliegue local* y *Tema 16. Despliegue en la nube* (Tecmilenio, 2026).
- Google Cloud: https://docs.cloud.google.com/run/docs/building/containers
- Google Cloud: https://docs.cloud.google.com/run/docs/deploying
- ISO/IEC 23053:2022, marco para sistemas de IA basados en machine learning. La estructura documental de este repositorio es orientativa y no implica certificación.
