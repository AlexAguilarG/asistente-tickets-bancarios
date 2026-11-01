# Publicar el repositorio en GitHub

## Preparación

1. Utiliza el ZIP `Asistente_Tickets_Despliegue_LISTO.zip` generado por Colab. Debe incluir el `.joblib`, `model_manifest.json` y `requirements-runtime.lock`.
2. Revisa `.gitignore`; nunca agregues `.env`, tokens, bases MLflow, datos crudos o tickets reales.
3. Confirma que el archivo serializado propio puede publicarse y que su tamaño no excede los límites de GitHub. Si es grande, usa Git LFS o almacenamiento privado.

## Crear repo y subir

Crea un repositorio vacío en GitHub, por ejemplo `asistente-tickets-bancarios`, sin inicializar README ni licencia si ya están incluidos localmente.

```bash
git init
git add .
git status
git commit -m "feat: despliegue local y API del asistente de tickets"
git branch -M main
git remote add origin https://github.com/<USUARIO>/asistente-tickets-bancarios.git
git push -u origin main
```

## Evidencias

- URL pública o privada del repositorio (según política).
- Vista de archivos: `Dockerfile`, `docker-compose.yml`, `app/`, `models/`, `docs/`, `tests/` y notebook de exportación.
- Resultado de Actions (`tests.yml`) en verde.
- Tag y salida de `docker images` local.
- Captura de interfaz y Swagger con mensaje ficticio.

## Revisión de secretos

Antes del push:

```bash
git status --short
git ls-files | findstr /i "\.env mlflow.db datos_raw tickets"
```

En macOS/Linux, sustituye `findstr` por `grep -Ei`. Si se detectó un secreto, eliminarlo del historial y revocar/rotar la credencial; no basta con borrar la última copia.
