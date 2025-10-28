#!/bin/bash

# Script para desplegar el backend de Software-SUNAT a Google Cloud Run

set -e  # Salir si hay error

echo "🚀 Desplegando Backend de Software-SUNAT a Cloud Run..."

# Configuración
PROJECT_ID="operaciones-peru"  # Reemplazar con tu project ID
SERVICE_NAME="sunat-backend"
REGION="us-central1"  # o tu región preferida

# 1. Configurar el proyecto
echo "📦 Configurando proyecto GCP..."
gcloud config set project $PROJECT_ID

# 2. Construir la imagen de Docker
echo "🏗️  Construyendo imagen Docker..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# 3. Desplegar a Cloud Run
echo "☁️  Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_NAME=$DB_NAME,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME" \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10

# 4. Obtener la URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "✅ Despliegue completado!"
echo "🌐 URL del backend: $SERVICE_URL"
echo ""
echo "⚠️  IMPORTANTE: Copia esta URL y actualiza:"
echo "   1. Software-SUNAT/frontend/.env.production con VITE_API_BASE_URL=$SERVICE_URL"
echo "   2. Rebuild y redeploy el frontend"
