# Backend image: FastAPI app (also runs the MCP server via a different CMD/entrypoint override).
FROM python:3.11-slim AS base

WORKDIR /app

# System deps kept minimal on purpose — no compiler toolchain needed for the
# pinned dependency set (pure-Python + prebuilt wheels).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY README.md ./

RUN pip install --no-cache-dir .

# Non-root user (security requirement).
RUN useradd --create-home --shell /bin/bash researchforge
USER researchforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "researchforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
