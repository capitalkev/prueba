#!/bin/bash

# ============================================================================
# Script de Deploy RÁPIDO - Solo actualiza configuración (NO rebuild)
# ============================================================================
# Usa la imagen existente, solo cambia env vars, memoria, etc.
# Tiempo: ~10-15 segundos
# ============================================================================

set -e

echo "============================================================================"
echo "ACTUALIZANDO CONFIGURACIÓN (SIN REBUILD)"
echo "============================================================================"
echo ""

# Variables
PROJECT_ID="operaciones-peru"
SERVICE_NAME="crm-sunat-backend"
REGION="southamerica-west1"
CLOUD_SQL_INSTANCE="operaciones-peru:southamerica-west1:crm-sunat"

echo "Configurando proyecto..."
gcloud config set project $PROJECT_ID

echo ""
echo "Actualizando servicio Cloud Run..."
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --add-cloudsql-instances $CLOUD_SQL_INSTANCE \
  --set-env-vars DB_USER=postgres,DB_NAME=CRM-SUNAT,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE \
  --set-secrets DB_PASSWORD=DB_PASSWORD:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

echo ""
echo "✅ Configuración actualizada en ~10-15 segundos"
echo ""
