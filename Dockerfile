FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    HF_HOME=/home/app/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1 \
    CONFIDENCE_THRESHOLD=0.50 \
    MODEL_DEVICE=cpu

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /home/app/.cache/huggingface

COPY requirements.txt ./
COPY requirements-runtime.lock* /tmp/locks/

RUN test -s /tmp/locks/requirements-runtime.lock || \
      (echo "Falta requirements-runtime.lock. Ejecuta el notebook de exportación de Colab." && exit 1) \
    && pip install --no-cache-dir -r /tmp/locks/requirements-runtime.lock

COPY app ./app
COPY models ./models

RUN test -s models/logistic_regression_classifier.joblib || \
    (echo "Falta el clasificador exportado." && exit 1) \
    && test -s models/model_manifest.json || \
    (echo "Falta model_manifest.json." && exit 1)

ARG PRELOAD_ENCODER=true

RUN if [ "${PRELOAD_ENCODER}" = "true" ]; then \
    python -c "import json; from sentence_transformers import SentenceTransformer; m=json.load(open('models/model_manifest.json', encoding='utf-8')); SentenceTransformer(m['encoder_id'], revision=m.get('encoder_revision') or None, device='cpu')"; \
    fi

RUN chown -R app:app /app /home/app/.cache

USER 10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').getenv('PORT','8080') + '/healthz', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
