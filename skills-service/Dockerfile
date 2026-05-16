FROM python:3.12-slim

# System deps minimales (pour httpx, anthropic, boto3, structlog)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Outils Python
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies (séparé de COPY src pour cache Docker)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

# Copier le code
COPY src ./src

# Sécurité : utilisateur non-root
RUN useradd -m -u 10001 skills && chown -R skills:skills /app
USER skills

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
