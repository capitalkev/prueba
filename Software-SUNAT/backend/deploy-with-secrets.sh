#!/bin/bash

# Script para desplegar el backend de Software-SUNAT a Google Cloud Run
# Usa Secret Manager de GCP en lugar de variables de entorno

set -e  # Salir si hay error

echo "🚀 Desplegando Backend de Software-SUNAT a Cloud Run..."

# ============ CONFIGURACIÓN ============
PROJECT_ID="operaciones-peru"
PROJECT_NUMBER="598125168090"
SERVICE_NAME="sunat-backend"
REGION="southamerica-west1"  # Santiago

# Cloud SQL Configuration
CLOUD_SQL_INSTANCE="crm-sunat"
CLOUD_SQL_CONNECTION_NAME="$PROJECT_ID:$REGION:$CLOUD_SQL_INSTANCE"

# Database credentials
DB_NAME="CRM-SUNAT"
DB_USER="postgres"

echo "📋 Configuración:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Cloud SQL: $CLOUD_SQL_CONNECTION_NAME"
echo "   Secret: DB_PASSWORD (desde Secret Manager)"
echo ""

# ============ 1. CONFIGURAR PROYECTO ============
echo "📦 Configurando proyecto GCP..."
gcloud config set project $PROJECT_ID

# ============ 2. HABILITAR APIs NECESARIAS ============
echo "🔧 Verificando APIs habilitadas..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# ============ 3. CONSTRUIR IMAGEN ============
echo "🏗️  Construyendo imagen Docker..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# ============ 4. DESPLEGAR A CLOUD RUN ============
echo "☁️  Desplegando a Cloud Run con Secret Manager..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $CLOUD_SQL_CONNECTION_NAME \
  --set-env-vars "DB_USER=$DB_USER,DB_NAME=$DB_NAME,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME" \
  --set-secrets "DB_PASSWORD=DB_PASSWORD:latest" \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --port 8080

# ============ 5. OBTENER URL ============
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo "✅ ¡Despliegue completado exitosamente!"
echo ""
echo "🌐 URL del backend: $SERVICE_URL"
echo ""
echo "📝 PRÓXIMOS PASOS:"
echo "   1. Verifica que el backend funciona:"
echo "      curl $SERVICE_URL/health"
echo ""
echo "   2. Redespliega el frontend (ya tiene la URL correcta):"
echo "      cd ../../verificador-frontend"
echo "      ./deploy.sh   # o deploy.ps1 en Windows"
echo ""
