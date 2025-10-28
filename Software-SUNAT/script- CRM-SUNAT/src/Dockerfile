# Dockerfile para Google Cloud Run - CRM SUNAT
# Actualización automática de datos SUNAT SIRE con FastAPI

FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar archivos Python necesarios (NO copiar CSVs ni backups)
COPY *.py ./

# Crear directorio para archivos temporales
RUN mkdir -p auxiliares

# Variables de entorno (se sobrescriben en Cloud Run)
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MAX_WORKERS=3

# Exponer puerto para Cloud Run
EXPOSE 8080

# Health check (opcional, pero recomendado)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Comando de ejecución usando Uvicorn (servidor ASGI para FastAPI)
CMD exec uvicorn app_cloud_run:app --host 0.0.0.0 --port ${PORT} --workers 1
