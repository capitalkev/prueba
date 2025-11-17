#!/bin/bash

# ============================================================================
# Script de Despliegue OPTIMIZADO del Backend a Google Cloud Run
# ============================================================================
# Usa Docker local con caché para builds rápidos
# ============================================================================

set -e  # Salir si hay errores

echo "============================================================================"
echo "DESPLEGANDO BACKEND A CLOUD RUN (OPTIMIZADO CON CACHÉ)"
echo "============================================================================"
echo ""

# Variables (ajustar según tu proyecto)
PROJECT_ID="operaciones-peru"
SERVICE_NAME="crm-sunat-backend"
REGION="southamerica-west1"
CLOUD_SQL_INSTANCE="operaciones-peru:southamerica-west1:crm-sunat"

# Artifact Registry (recomendado sobre Container Registry)
REPOSITORY="cloud-run-images"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "1. Configuración:"
echo "   - Proyecto: $PROJECT_ID"
echo "   - Servicio: $SERVICE_NAME"
echo "   - Región: $REGION"
echo "   - Cloud SQL: $CLOUD_SQL_INSTANCE"
echo "   - Imagen: $FULL_IMAGE_NAME"
echo ""

# Configurar proyecto
echo "2. Configurando proyecto GCP..."
gcloud config set project $PROJECT_ID
echo "   ✓ Proyecto configurado"
echo ""

# Asegurar que Artifact Registry existe
echo "3. Verificando Artifact Registry..."
if ! gcloud artifacts repositories describe $REPOSITORY --location=$REGION &>/dev/null; then
  echo "   ℹ Creando repositorio en Artifact Registry..."
  gcloud artifacts repositories create $REPOSITORY \
    --repository-format=docker \
    --location=$REGION \
    --description="Imágenes Docker para Cloud Run"
  echo "   ✓ Repositorio creado"
else
  echo "   ✓ Repositorio existe"
fi
echo ""

# Configurar Docker para autenticar con Artifact Registry
echo "4. Configurando autenticación Docker..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
echo "   ✓ Docker configurado"
echo ""

# Build local (aprovecha caché de Docker)
echo "5. Construyendo imagen Docker LOCALMENTE (con caché)..."
docker build --platform linux/amd64 -t $FULL_IMAGE_NAME .
echo "   ✓ Imagen construida"
echo ""

# Push a Artifact Registry
echo "6. Subiendo imagen a Artifact Registry..."
docker push $FULL_IMAGE_NAME
echo "   ✓ Imagen subida"
echo ""

# Deploy a Cloud Run (desde imagen pre-construida)
echo "7. Desplegando a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $FULL_IMAGE_NAME \
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
echo "💡 TIPS:"
echo "   - Los siguientes deploys serán MUY rápidos (solo se reconstruyen capas modificadas)"
echo "   - Si solo cambias código Python, el build tardará ~10-20 segundos"
echo "   - Si no cambias requirements.txt, la capa de pip install se reutiliza"
echo ""
