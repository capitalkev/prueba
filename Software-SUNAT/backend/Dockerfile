FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto (Cloud Run usa la variable PORT, default 8080)
ENV PORT=8080
EXPOSE 8080

# Comando para ejecutar la aplicación (sin --reload en producción)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
