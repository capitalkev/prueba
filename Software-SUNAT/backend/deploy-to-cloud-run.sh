#!/bin/bash

# Script para desplegar el backend de Software-SUNAT a Google Cloud Run
# Conectado a Cloud SQL existente

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
DB_USER="postgres"  # Ajustar si es diferente
# DB_PASSWORD se debe pasar como variable de entorno o usar Secret Manager

echo "📋 Configuración:"
echo "   Project: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Cloud SQL: $CLOUD_SQL_CONNECTION_NAME"
echo ""

# ============ VERIFICAR REQUISITOS ============
if [ -z "$DB_PASSWORD" ]; then
    echo "⚠️  ERROR: La variable DB_PASSWORD no está configurada"
    echo "   Ejecútala así: DB_PASSWORD='tu_password' ./deploy-to-cloud-run.sh"
    exit 1
fi

# ============ 1. CONFIGURAR PROYECTO ============
echo "📦 Configurando proyecto GCP..."
gcloud config set project $PROJECT_ID

# ============ 2. HABILITAR APIs NECESARIAS ============
echo "🔧 Verificando APIs habilitadas..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    --quiet

# ============ 3. CONSTRUIR IMAGEN ============
echo "🏗️  Construyendo imagen Docker..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# ============ 4. DESPLEGAR A CLOUD RUN ============
echo "☁️  Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $CLOUD_SQL_CONNECTION_NAME \
  --set-env-vars "DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_NAME=$DB_NAME,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME" \
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
echo "   2. Actualiza Software-SUNAT/frontend/.env.production:"
echo "      VITE_API_BASE_URL=$SERVICE_URL"
echo ""
echo "   3. Reconstruye y redespliega el frontend completo:"
echo "      cd ../../verificador-frontend"
echo "      ./deploy.ps1"
echo ""
