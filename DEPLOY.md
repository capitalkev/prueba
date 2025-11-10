# Guía de Despliegue - Operaciones Perú

Este repositorio contiene tres aplicaciones independientes. Esta guía explica cómo desplegar cada una.

## Arquitectura de Despliegue

### Frontend
- **verificador-frontend**: Aplicación React unificada desplegada en Firebase Hosting
  - Raíz del dominio: Dashboard de operaciones
  - Ruta `/sunat`: Módulo de Software SUNAT integrado
- Proyecto Firebase: `operaciones-peru`

### Backend
- **gcp-microservicios/orquestador-service**: Backend principal (Cloud Run)
- **Software-SUNAT/backend**: Backend de facturas SUNAT (Cloud Run)
- **Cloud SQL**: Base de datos PostgreSQL compartida (`crm-sunat`)

## URLs de Producción

### Frontend
- Verificador: `https://operaciones-peru.web.app`
- Software SUNAT: `https://operaciones-peru.web.app/sunat`

### Backend
- Orquestador: `https://orquestador-service-598125168090.southamerica-west1.run.app`
- SUNAT Backend: `https://sunat-backend-598125168090.southamerica-west1.run.app`

## Requisitos Previos

1. Node.js instalado
2. Firebase CLI instalado: `npm install -g firebase-tools`
3. Autenticación con Firebase: `firebase login`
4. Google Cloud SDK instalado (para backend): `gcloud auth login`

---

## Despliegue Frontend (verificador-frontend)

El frontend es una aplicación React unificada que incluye:
- Dashboard de operaciones de factoring
- Gestión de operaciones
- Software SUNAT integrado en `/sunat`

### Opción 1: Script Automático (Windows)

```powershell
cd verificador-frontend
.\deploy.ps1
```

### Opción 2: Script Automático (Linux/Mac)

```bash
cd verificador-frontend
chmod +x deploy.sh
./deploy.sh
```

### Opción 3: Manual

```bash
# 1. Compilar verificador-frontend
cd verificador-frontend
npm run build

# 2. Desplegar a Firebase
firebase deploy --only hosting
```

**Nota**: El módulo Software-SUNAT está integrado en `verificador-frontend/src/pages/Sunat/` y se compila automáticamente junto con el resto de la aplicación.

---

## Despliegue Backend Software-SUNAT

El backend de Software-SUNAT se despliega en Google Cloud Run.

### Pasos para Desplegar

**Windows:**
```powershell
cd Software-SUNAT/backend
$env:DB_PASSWORD = "Crm-sunat1"
.\deploy-to-cloud-run.ps1
```

**Linux/Mac:**
```bash
cd Software-SUNAT/backend
export DB_PASSWORD="Crm-sunat1"
chmod +x deploy-to-cloud-run.sh
./deploy-to-cloud-run.sh
```

Ver documentación detallada: [Software-SUNAT/DEPLOY-BACKEND.md](Software-SUNAT/DEPLOY-BACKEND.md)

### Actualizar URL del Backend en Frontend

Después de desplegar el backend por primera vez, verifica que la URL esté configurada correctamente en:

`verificador-frontend/src/pages/Sunat/constants/index.js`:

```javascript
export const API_BASE_URL = 'https://sunat-backend-598125168090.southamerica-west1.run.app';
```

Si cambias esta URL, necesitas redesplegar el frontend.

---

## Despliegue Backend Orquestador (gcp-microservicios)

Los microservicios se despliegan en Google Cloud Run. Cada servicio tiene su propio Dockerfile.

### Ejemplo: Desplegar Orquestador

```bash
cd gcp-microservicios/orquestador-service

# Build y push de la imagen
gcloud builds submit --tag gcr.io/operaciones-peru/orquestador-service

# Deploy a Cloud Run
gcloud run deploy orquestador-service \
  --image gcr.io/operaciones-peru/orquestador-service \
  --platform managed \
  --region southamerica-west1 \
  --allow-unauthenticated
```

Ver documentación detallada en: `gcp-microservicios/orquestador-service/ARCHITECTURE.md`

---

## Flujo de Usuario

1. Usuario ingresa a `operaciones-peru.web.app` → Ve **Dashboard de Operaciones**
2. Navega a `/sunat` o hace clic en "Software SUNAT" → Ve **Dashboard de Facturas SUNAT**
3. Ambas vistas requieren autenticación Firebase

---

## Desarrollo Local

### Frontend Unificado

```bash
cd verificador-frontend
npm install
npm run dev
# Abre en http://localhost:5173
# - Ruta raíz: Dashboard de operaciones
# - Ruta /sunat: Software SUNAT
```

### Backend Software-SUNAT

```bash
cd Software-SUNAT/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API disponible en http://localhost:8000
# Docs en http://localhost:8000/docs
```

### Backend Orquestador

```bash
cd gcp-microservicios/orquestador-service
pip install -r requirements.txt
python main.py
# API disponible en http://localhost:8080
```

---

## Arquitectura del Frontend Unificado

```
verificador-frontend/
├── src/
│   ├── App.jsx                    # Router principal
│   ├── pages/
│   │   ├── Dashboard.jsx          # /dashboard (ventas)
│   │   ├── Gestiones.jsx          # /gestion
│   │   ├── NewOperationPage.jsx   # /new-operation
│   │   ├── SunatPage.jsx          # /sunat (wrapper)
│   │   └── Sunat/                 # Módulo Software-SUNAT integrado
│   │       ├── App.jsx            # Componente principal de SUNAT
│   │       ├── components/
│   │       ├── constants/
│   │       └── utils/
│   ├── context/
│   │   └── AuthContext.jsx        # Autenticación Firebase (compartida)
│   └── firebase.js                # Configuración Firebase (compartida)
```

**Beneficios de la arquitectura unificada:**
- ✅ Un solo despliegue para todo el frontend
- ✅ Autenticación Firebase compartida
- ✅ Sin necesidad de copiar builds entre proyectos
- ✅ Código más fácil de mantener

---

## Troubleshooting

### El módulo SUNAT no carga en /sunat

**Solución:**
1. Verifica que `src/pages/Sunat/App.jsx` existe
2. Verifica que `src/pages/SunatPage.jsx` importa correctamente
3. Verifica que la ruta `/sunat` está en `App.jsx`
4. Recompila: `npm run build && firebase deploy --only hosting`

### Error 404 en Firebase

**Solución:**
- Verifica que `firebase.json` tenga el rewrite correcto
- Redespliega: `firebase deploy --only hosting`

### Backend de SUNAT no responde

**Solución:**
1. Verifica que Cloud Run está corriendo:
   ```bash
   gcloud run services list --region southamerica-west1
   ```
2. Revisa logs:
   ```bash
   gcloud run logs read sunat-backend --region southamerica-west1
   ```
3. Verifica la URL en `verificador-frontend/src/pages/Sunat/constants/index.js`

### Software-SUNAT muestra error de autenticación

**Solución:**
- El módulo SUNAT usa el mismo `AuthContext` que el resto de verificador-frontend
- Verifica que Firebase está configurado correctamente en `src/firebase.js`
- Cierra sesión y vuelve a iniciar

---

## Resumen de Comandos Rápidos

```bash
# Deploy frontend completo
cd verificador-frontend && npm run build && firebase deploy --only hosting

# Deploy backend SUNAT
cd Software-SUNAT/backend && gcloud builds submit --tag gcr.io/operaciones-peru/sunat-backend

# Ver logs de frontend
firebase hosting:channel:list

# Ver logs de backend
gcloud run logs tail sunat-backend --region southamerica-west1
```

---

## Contacto y Soporte

Para problemas o preguntas sobre el despliegue, consulta:
- CLAUDE.md (guía completa de desarrollo)
- Software-SUNAT/DEPLOY-BACKEND.md (backend SUNAT específico)
- gcp-microservicios/orquestador-service/ARCHITECTURE.md (microservicios)
