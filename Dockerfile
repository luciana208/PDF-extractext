FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración
COPY pyproject.toml .
COPY README.md .

# Instalar solo dependencias de producción
RUN uv pip install --system -e .

# Copiar código fuente
COPY app/ ./app/

# Variables de entorno
ENV MONGO_URL=mongodb://mongo:27017
ENV DB_NAME=pdf_extraction_db
ENV MAX_PDF_SIZE_MB=10
ENV DEFAULT_PAGE_SIZE=20
ENV MAX_PAGE_SIZE=100

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]