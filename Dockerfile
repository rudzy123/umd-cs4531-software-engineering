FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TASK_API_ENVIRONMENT=production \
    TASK_API_LOG_LEVEL=INFO \
    TASK_API_DATABASE_URL=sqlite:////data/tasks.db

WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "task_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
