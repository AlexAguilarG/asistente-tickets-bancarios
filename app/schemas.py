from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=3, max_length=5000, description="Texto del ticket, anonimizado y sin datos sensibles.")

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("El texto no puede estar vacío ni contener solo espacios.")
        return normalized


class PredictionResponse(BaseModel):
    model_name: str
    predicted_intent_id: int
    predicted_intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    decision: str
    requires_human_review: bool
    priority_assigned: str | None = None
    priority_note: str
    disclaimer: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str | None = None
    detail: str | None = None
