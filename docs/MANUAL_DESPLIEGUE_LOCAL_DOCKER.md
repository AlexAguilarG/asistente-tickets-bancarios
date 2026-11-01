# Manual de despliegue local con Docker

## 1. Requisitos previos

- Windows 10/11 con Docker Desktop y WSL 2, o macOS/Linux con Docker Engine.
- 8 GB de RAM como referencia mínima para probar; 16 GB recomendados para mayor comodidad.
- Conexión a internet en la primera ejecución para descargar el encoder MiniLM desde Hugging Face.
- Artefacto propio `models/logistic_regression_classifier.joblib`, catálogo `models/intent_labels.json` y manifiesto `models/model_manifest.json`.
- `requirements-runtime.lock` generado desde el runtime que produjo el clasificador. El ZIP inicial incorpora el notebook que genera esos archivos.

> Docker no se ejecuta dentro del flujo normal de Google Colab. Colab se utiliza para exportar el artefacto y sus versiones; la construcción y ejecución del contenedor se realizan en una computadora con Docker Desktop o en un servicio de construcción de contenedores.

## 2. Exportar el modelo desde Colab

1. Descarga `Asistente_Tickets_Despliegue.zip` y súbelo a Google Colab.
2. Descomprímelo en `/content/Asistente_Tickets_Despliegue`.
3. Abre y ejecuta `notebooks/EXPORTAR_MODELO_DESDE_COLAB.ipynb`.
4. El notebook monta Google Drive y busca `Actividad5/modelos/logistic_regression_classifier.joblib`.
5. Copia el clasificador a `models/`, vuelve a generar el catálogo JSON a partir del diccionario de 77 intenciones, y crea el manifiesto y `requirements-runtime.lock`.
6. Descarga el archivo `Asistente_Tickets_Despliegue_LISTO.zip` generado por Colab.

Si no encuentra el `.joblib`, el notebook se detiene sin entrenar. Regresa al notebook Actividad 6 y confirma que el modelo se haya guardado en `Actividad5/modelos/`.

## 3. Construir la imagen

Descomprime el paquete LISTO en tu computadora, abre PowerShell/Terminal en la raíz del proyecto y ejecuta:

```bash
python scripts/verify_artifacts.py
docker build --build-arg PRELOAD_ENCODER=true -t asistente-tickets:1.0.0 .
```

El Dockerfile utiliza Python 3.13 slim, instala dependencias, copia la API, interfaz y artefactos, y ejecuta el servicio con un usuario sin privilegios. El build falla intencionalmente si no encuentra el clasificador exportado.

## 4. Ejecutar el contenedor

```bash
docker run --rm --name asistente-tickets \
  -p 8080:8080 \
  -e CONFIDENCE_THRESHOLD=0.50 \
  -e MODEL_DEVICE=cpu \
  -v tickets-hf-cache:/home/app/.cache/huggingface \
  asistente-tickets:1.0.0
```

En PowerShell de Windows puede usarse el comando equivalente en una sola línea:

```powershell
docker run --rm --name asistente-tickets -p 8080:8080 -e CONFIDENCE_THRESHOLD=0.50 -e MODEL_DEVICE=cpu -v tickets-hf-cache:/home/app/.cache/huggingface asistente-tickets:1.0.0
```

El build descarga el encoder MiniLM desde Hugging Face y lo almacena en la imagen para evitar una descarga en cada arranque. El primer build puede tardar y generar una imagen más grande. El volumen `tickets-hf-cache` conserva la caché disponible para futuras ejecuciones.

## 5. Verificar la aplicación

- Interfaz: http://localhost:8080/
- Documentación Swagger de la API: http://localhost:8080/docs
- Liveness: http://localhost:8080/healthz
- Readiness del modelo: http://localhost:8080/readyz
- Metadatos: http://localhost:8080/api/metadata

Prueba de inferencia con cURL:

```bash
curl -X POST "http://localhost:8080/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"text":"Mi transferencia no llegó al destinatario"}'
```

PowerShell:

```powershell
$body = @{ text = "Mi transferencia no llegó al destinatario" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/predict -ContentType "application/json" -Body $body
```

La respuesta debe contener `predicted_intent_id`, `predicted_intent`, `confidence`, `decision` y `requires_human_review`. La etiqueta que devuelva el modelo debe verificarse contra el criterio de negocio; no se exige que una frase de ejemplo produzca una clase específica como prueba unitaria.

## 6. Ejecutar con Docker Compose

```bash
docker compose up --build
```

Para detener:

```bash
docker compose down
```

El volumen de caché se conserva, salvo que se elimine explícitamente con `docker volume rm`.

## 7. Revisar logs y estado

```bash
docker ps
docker logs asistente-tickets
docker inspect --format='{{.State.Health.Status}}' asistente-tickets
```

Los logs no deben contener mensajes completos de tickets. Si `/healthz` responde pero `/readyz` devuelve `503`, revisar el log de inicio, la ruta del `.joblib`, el manifiesto y la descarga del encoder.
