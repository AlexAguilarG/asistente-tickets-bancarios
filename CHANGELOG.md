# Changelog

## 1.0.0 - 2026-10-31

- Se incorpora API FastAPI y frontend web para el pipeline MiniLM + Regresión Logística.
- Se agregan endpoints de liveness, readiness, metadata y predicción.
- Se incorpora Dockerfile, Compose y plantilla Cloud Build para Cloud Run.
- Se agrega notebook Colab para exportar el artefacto real sin reentrenar y fijar versiones runtime.
- Se incluyen pruebas del contrato HTTP, manuales y documentación de límites.
- Pendiente: artefacto joblib real del Drive del usuario, build/ejecución Docker en equipo local, publicación GitHub y deploy Cloud Run.
