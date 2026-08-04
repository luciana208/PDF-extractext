FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias en producción
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de definición de dependencias primero para aprovechar cache
# y asegurar reproducibilidad con uv.lock si está presente.
COPY pyproject.toml uv.lock* ./

# Instalar dependencias usando `uv sync --frozen` para fijar versiones transitivas
RUN if [ -f uv.lock ]; then uv sync --frozen; else uv sync; fi

# Copiar el código de la aplicación después de instalar dependencias
COPY app/ ./app/

# Crear usuario no-root y asegurar permisos sobre el directorio de trabajo
RUN groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]