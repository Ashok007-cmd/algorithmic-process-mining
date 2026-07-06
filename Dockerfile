# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: Final
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends graphviz curl && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src/ src/
COPY pyproject.toml README.md ./

RUN chown -R app:app /app
USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# NOTE: this exposes the dashboard on all interfaces with no authentication.
# Front it with a reverse proxy that provides TLS + auth before exposing it
# outside a trusted network.
CMD ["streamlit", "run", "src/viz/dashboard.py", "--server.address=0.0.0.0"]
