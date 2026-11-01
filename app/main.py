from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    AUTO_LOAD_MODEL,
    CONFIDENCE_THRESHOLD,
    DEVICE,
    ENCODER_ID,
    INTENT_LABELS_PATH,
    MANIFEST_PATH,
    MAX_TEXT_LENGTH,
    MODEL_PATH,
)
from app.predictor import TicketClassifier
from app.schemas import HealthResponse, PredictionRequest, PredictionResponse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ticket-api")
STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(predictor: Any | None = None, auto_load: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.predictor = predictor
        application.state.model_error = None
        if predictor is None and auto_load and AUTO_LOAD_MODEL:
            try:
                application.state.predictor = TicketClassifier.load_from_files(
                    model_path=MODEL_PATH,
                    labels_path=INTENT_LABELS_PATH,
                    manifest_path=MANIFEST_PATH,
                    confidence_threshold=CONFIDENCE_THRESHOLD,
                    device=DEVICE,
                    encoder_id_override=ENCODER_ID,
                )
                logger.info("Pipeline de clasificación cargado correctamente.")
            except Exception as exc:  # La app sigue viva para diagnóstico; /readyz devuelve 503.
                application.state.model_error = str(exc)
                logger.exception("No fue posible cargar el pipeline del modelo.")
        yield

    application = FastAPI(
        title="Asistente de tickets bancarios",
        version="1.0.0",
        description=(
            "API académica para sugerir una intención de entre 77 categorías. "
            "No asigna prioridad y no sustituye la validación humana."
        ),
        lifespan=lifespan,
    )

    origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization"],
        )

    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @application.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/readyz", response_model=HealthResponse)
    def readyz() -> HealthResponse:
        loaded = application.state.predictor is not None
        if not loaded:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "model_loaded": False,
                    "detail": application.state.model_error or "El modelo todavía no está disponible.",
                },
            )
        return HealthResponse(status="ready", model_loaded=True, model_name="logistic_regression")

    @application.get("/api/metadata")
    def metadata() -> dict[str, Any]:
        loaded = application.state.predictor is not None
        return {
            "application": "Asistente de clasificación de tickets",
            "model_name": "logistic_regression",
            "encoder_id": ENCODER_ID,
            "number_of_intents": 77,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "model_loaded": loaded,
            "priority_automation": False,
            "max_text_length": MAX_TEXT_LENGTH,
            "scope": "prototipo académico; no producción bancaria",
        }

    @application.post("/api/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest) -> PredictionResponse:
        if len(request.text) > MAX_TEXT_LENGTH:
            raise HTTPException(status_code=422, detail=f"El texto supera el límite de {MAX_TEXT_LENGTH} caracteres.")
        active_predictor = application.state.predictor
        if active_predictor is None:
            raise HTTPException(
                status_code=503,
                detail="Modelo no disponible. Comprueba el artefacto .joblib y el arranque del servicio.",
            )
        try:
            result = active_predictor.predict(request.text)
            return PredictionResponse(**result)
        except HTTPException:
            raise
        except Exception as exc:
            # No registrar el cuerpo del ticket ni datos personales.
            logger.exception("Error durante la inferencia; el texto recibido no se registra.")
            raise HTTPException(status_code=500, detail="No fue posible clasificar el ticket.") from exc

    return application


app = create_app()
