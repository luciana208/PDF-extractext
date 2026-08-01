FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias en producción
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar la configuración del proyecto y el código fuente antes de instalar
COPY pyproject.toml .
COPY app/ ./app/

# Instalar solo dependencias de producción
RUN uv pip install --system -e .

# Crear usuario no-root y asegurar permisos sobre el directorio de trabajo
RUN groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV MONGO_URL=mongodb://mongo:27017
ENV DB_NAME=pdf_extraction_db
ENV MAX_PDF_SIZE_MB=10
ENV DEFAULT_PAGE_SIZE=20
ENV MAX_PAGE_SIZE=100

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]