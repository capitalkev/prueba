#!/bin/bash

# ============================================================================
# Script de Despliegue del Backend a Google Cloud Run
# ============================================================================
# Despliega la corrección de notas de crédito a producción
# ============================================================================

set -e  # Salir si hay errores

echo "============================================================================"
echo "DESPLEGANDO BACKEND A CLOUD RUN"
echo "============================================================================"
echo ""

# Variables (ajustar según tu proyecto)
PROJECT_ID="operaciones-peru"
SERVICE_NAME="backend-crm-sunat"
REGION="southamerica-west1"
CLOUD_SQL_INSTANCE="operaciones-peru:southamerica-west1:crm-sunat"

echo "1. Configuración:"
echo "   - Proyecto: $PROJECT_ID"
echo "   - Servicio: $SERVICE_NAME"
echo "   - Región: $REGION"
echo "   - Cloud SQL: $CLOUD_SQL_INSTANCE"
echo ""

# Configurar proyecto
echo "2. Configurando proyecto GCP..."
gcloud config set project $PROJECT_ID
echo "   ✓ Proyecto configurado"
echo ""

# Build y despliegue
echo "3. Construyendo y desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances $CLOUD_SQL_INSTANCE \
  --set-env-vars DB_USER=postgres,DB_NAME=CRM-SUNAT,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE \
  --set-secrets DB_PASSWORD=DB_PASSWORD:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

echo ""
echo "============================================================================"
echo "✅ DESPLIEGUE COMPLETADO"
echo "============================================================================"
echo ""
echo "SIGUIENTE PASO:"
echo "Verificar el servicio en:"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
echo ""
