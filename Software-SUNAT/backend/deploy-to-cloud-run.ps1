# Script para desplegar el backend de Software-SUNAT a Google Cloud Run
# Conectado a Cloud SQL existente

$ErrorActionPreference = "Stop"

Write-Host "🚀 Desplegando Backend de Software-SUNAT a Cloud Run..." -ForegroundColor Green

# ============ CONFIGURACIÓN ============
$PROJECT_ID = "operaciones-peru"
$PROJECT_NUMBER = "598125168090"
$SERVICE_NAME = "sunat-backend"
$REGION = "southamerica-west1"  # Santiago

# Cloud SQL Configuration
$CLOUD_SQL_INSTANCE = "crm-sunat"
$CLOUD_SQL_CONNECTION_NAME = "${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}"

# Database credentials
$DB_NAME = "CRM-SUNAT"
$DB_USER = "postgres"
$DB_PASSWORD = $env:DB_PASSWORD

Write-Host "📋 Configuración:" -ForegroundColor Cyan
Write-Host "   Project: $PROJECT_ID"
Write-Host "   Service: $SERVICE_NAME"
Write-Host "   Region: $REGION"
Write-Host "   Cloud SQL: $CLOUD_SQL_CONNECTION_NAME"
Write-Host ""

# ============ VERIFICAR REQUISITOS ============
if ([string]::IsNullOrEmpty($DB_PASSWORD)) {
    Write-Host "⚠️  ERROR: La variable DB_PASSWORD no está configurada" -ForegroundColor Red
    Write-Host "   Ejecútala así: `$env:DB_PASSWORD='Crm-sunat1'; .\deploy-to-cloud-run.ps1"
    exit 1
}

# ============ 1. CONFIGURAR PROYECTO ============
Write-Host "📦 Configurando proyecto GCP..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# ============ 2. HABILITAR APIs NECESARIAS ============
Write-Host "🔧 Verificando APIs habilitadas..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com sqladmin.googleapis.com --quiet

# ============ 3. CONSTRUIR IMAGEN ============
Write-Host "🏗️  Construyendo imagen Docker..." -ForegroundColor Cyan
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# ============ 4. DESPLEGAR A CLOUD RUN ============
Write-Host "☁️  Desplegando a Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --add-cloudsql-instances $CLOUD_SQL_CONNECTION_NAME `
  --set-env-vars "DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_NAME=$DB_NAME,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION_NAME" `
  --memory 1Gi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --timeout 300 `
  --port 8080

# ============ 5. OBTENER URL ============
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --format 'value(status.url)'

Write-Host ""
Write-Host "✅ ¡Despliegue completado exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URL del backend: $SERVICE_URL" -ForegroundColor White
Write-Host ""
Write-Host "📝 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "   1. Verifica que el backend funciona:"
Write-Host "      curl $SERVICE_URL/health"
Write-Host ""
Write-Host "   2. Actualiza Software-SUNAT/frontend/.env.production:"
Write-Host "      VITE_API_BASE_URL=$SERVICE_URL"
Write-Host ""
Write-Host "   3. Reconstruye y redespliega el frontend completo:"
Write-Host "      cd ..\..\verificador-frontend"
Write-Host "      .\deploy.ps1" -NoNewline
Write-Host ""
Write-Host ""
