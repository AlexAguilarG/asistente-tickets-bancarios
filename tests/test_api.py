from fastapi.testclient import TestClient

from app.main import create_app


class FakePredictor:
    def predict(self, text: str):
        return {
            "model_name": "logistic_regression",
            "predicted_intent_id": 66,
            "predicted_intent": "transfer_not_received_by_recipient",
            "confidence": 0.82,
            "confidence_threshold": 0.50,
            "decision": "suggestion",
            "requires_human_review": False,
            "priority_assigned": None,
            "priority_note": "La prioridad no se automatiza en esta versión.",
            "disclaimer": "Prototipo académico; no producción bancaria.",
        }


def make_client(predictor=None):
    return TestClient(create_app(predictor=predictor, auto_load=False))


def test_liveness_endpoint():
    with make_client(FakePredictor()) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_with_predictor():
    with make_client(FakePredictor()) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is True


def test_predict_returns_intent_and_human_review_fields():
    with make_client(FakePredictor()) as client:
        response = client.post("/api/predict", json={"text": "Mi transferencia no llegó al destinatario"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_intent_id"] == 66
    assert payload["predicted_intent"] == "transfer_not_received_by_recipient"
    assert 0.0 <= payload["confidence"] <= 1.0
    assert payload["priority_assigned"] is None


def test_empty_text_is_rejected():
    with make_client(FakePredictor()) as client:
        response = client.post("/api/predict", json={"text": "   "})
    assert response.status_code == 422


def test_too_short_text_is_rejected():
    with make_client(FakePredictor()) as client:
        response = client.post("/api/predict", json={"text": "a"})
    assert response.status_code == 422


def test_extra_fields_are_rejected():
    with make_client(FakePredictor()) as client:
        response = client.post("/api/predict", json={"text": "Consulta de ejemplo", "customer_id": "123"})
    assert response.status_code == 422


def test_missing_model_returns_503():
    with make_client(None) as client:
        response = client.post("/api/predict", json={"text": "Consulta de ejemplo"})
    assert response.status_code == 503


def test_frontend_is_served():
    with make_client(FakePredictor()) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Asistente de tickets" in response.text


def test_metadata_exposes_non_automated_priority():
    with make_client(FakePredictor()) as client:
        response = client.get("/api/metadata")
    assert response.status_code == 200
    assert response.json()["priority_automation"] is False
    assert response.json()["number_of_intents"] == 77


def test_text_over_limit_is_rejected():
    with make_client(FakePredictor()) as client:
        response = client.post("/api/predict", json={"text": "x" * 5001})
    assert response.status_code == 422


def test_readiness_without_predictor_returns_503():
    with make_client(None) as client:
        response = client.get("/readyz")
    assert response.status_code == 503
