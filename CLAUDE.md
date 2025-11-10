# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a multi-project repository for Peruvian operations management, containing three independent applications:

1. **Software-SUNAT/** - Tax compliance CRM for managing SUNAT (Peru tax authority) invoice data
2. **verificador-frontend/** - Operations verification dashboard with Firebase authentication
3. **gcp-microservicios/** - GCP-based microservices architecture for document processing and workflow automation

Each project is completely independent with its own tech stack, deployment, and purpose.

---

## 1. Software-SUNAT (Tax Compliance CRM)

### Purpose
Full-stack application that downloads purchase/sales records from SUNAT API, stores them in PostgreSQL, and provides a React dashboard to visualize invoice opportunities for factoring/financing.

**Note**: The frontend is now integrated into verificador-frontend at `/sunat` route. See section 2 for frontend details.

### Project Structure
- **CRM-SUNAT/** - Python scripts for SUNAT API data extraction
- **backend/** - FastAPI REST API with Repository Pattern
- **Frontend** - Integrated into verificador-frontend (see section 2)

### Key Commands

```bash
# Data Extraction Scripts
cd Software-SUNAT/CRM-SUNAT
python main.py                    # Initial 14-month historical load
python main_ultimo_mes.py         # Monthly updates (last completed month)
python cargar_csv_manual.py       # Manual CSV import
python create_tables.py           # Initialize database tables

# Backend API
cd Software-SUNAT/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000    # Development
python main.py                           # Production

# Frontend (integrated in verificador-frontend)
# See section 2 "verificador-frontend" for frontend commands
# Access at http://localhost:5173/sunat when running verificador-frontend dev server
```

### Architecture Overview

**Data Flow:**
1. Python scripts authenticate with SUNAT OAuth2 API and download CSV files
2. CSV data is parsed and inserted into PostgreSQL (SQLAlchemy ORM)
3. Backend API exposes paginated REST endpoints querying PostgreSQL
4. React frontend fetches and displays invoice pipeline with real-time metrics

**Multi-Company Management:**
- System manages multiple companies ("enrolados") with different SUNAT credentials
- `estado` field: "pendiente" (needs initial 14-month load) → "completo" (monthly updates only)
- `main.py` processes historical data for pendiente companies, current month for completo companies

**Key Database Models:**
- `Enrolado` - Companies with SUNAT credentials and OAuth tokens
- `VentaElectronica` / `CompraElectronica` - Sales/purchase invoice records
- `PeriodoFallido` - Tracks failed download attempts for troubleshooting

**Primary Backend Endpoints:**
- `GET /api/ventas` - Paginated sales with filters (ruc_empresa, periodo, fecha_desde/hasta, sort_by)
- `GET /api/metricas/{periodo}` - Metrics separated by currency (PEN/USD)
- `GET /api/estadisticas/resumen` - System-wide statistics
- `GET /api/enrolados` - List all enrolled companies

**Frontend Features:**
- Real-time invoice pipeline dashboard with 3 key metrics:
  1. Monto Ganado/Facturado - Progress bar showing conversion %
  2. Total Facturado (Soles) - Sum of PEN invoices
  3. Total Facturado (Dólares) - Sum of USD invoices
- Paginated table (20 items/page) with sortable columns
- Multi-client filtering with dropdown checkboxes
- Invoice status pipeline: Nueva Oportunidad → Contactado → Negociación → Ganada/Perdida

### SUNAT API Workflow

4-step OAuth2 + polling workflow:
1. **Authentication**: POST to `api-seguridad.sunat.gob.pe` with OAuth credentials
2. **Request Submission**: GET to SIRE API → returns ticket number
3. **Status Polling**: Poll every 5 seconds until status = "Terminado"
4. **Download**: GET ZIP file → extract CSV → parse → insert to database

Periods are formatted as `YYYYMM` (e.g., "202510" for October 2025).

### Environment Configuration

**CRM-SUNAT/.env** (per enrolado):
```env
CLIENT_RUC=         # Company RUC number
CLIENT_ID=          # SUNAT OAuth client ID
CLIENT_SECRET=      # SUNAT OAuth secret
USUARIO_SOL=        # SUNAT SOL portal username
CLAVE_SOL=          # SUNAT SOL portal password
COD_LIBRO_RCE=080000   # Purchases book code
COD_LIBRO_RVIE=140000  # Sales book code
DB_USER=            # PostgreSQL credentials
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crm_sunat
```

**backend/.env**:
```env
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crm_sunat
```

### Running the Full Stack

Prerequisites: PostgreSQL running with data populated by CRM-SUNAT scripts

```bash
# Terminal 1: Start backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend && npm run dev

# Access:
# - App: http://localhost:5173
# - API docs: http://localhost:8000/docs
```

---

## 2. verificador-frontend (Operations Dashboard)

### Purpose
React application for managing financial operations (factoring/financing) with role-based access control, Firebase authentication, and Google Sheets/Drive integration.

### Tech Stack
- React 19 + Vite
- TailwindCSS + Framer Motion
- React Router DOM for routing
- Firebase for authentication
- Google OAuth for additional integrations

### Key Commands

```bash
cd verificador-frontend

npm install
npm run dev         # Development (http://localhost:5173)
npm run build       # Production build
npm run preview     # Preview production build
npm run lint        # Run ESLint
```

### Application Structure

**Pages:**
- `LoginPage.jsx` - Firebase authentication login
- `Dashboard.jsx` - Main operations dashboard (ventas role)
- `Gestiones.jsx` - Operations management queue (gestion role)
- `NewOperationPage.jsx` - Form to create new operations
- `SunatPage.jsx` - Software-SUNAT module wrapper
- `Sunat/App.jsx` - Software-SUNAT dashboard (integrated module)

**Integrated Modules:**
- **Software-SUNAT** - Located in `src/pages/Sunat/`
  - Accessible via `/sunat` route
  - Uses shared Firebase authentication from parent app
  - Manages invoice pipeline and SUNAT tax compliance data
  - Components: `MultiClientSelector`, `MultiCurrencySelector`, `MetricCard`
  - Constants: `API_BASE_URL`, `STATUS_COLORS`, `INVOICE_STATUSES`
  - Utils: `formatCurrency`, `formatPeriodDisplay`

**Role-Based Access:**
- **admin** - Full access to all pages (sees navigation header)
- **ventas** - Access to Dashboard, NewOperation, and Sunat
- **gestion** - Access to Gestiones only
- Users redirected to appropriate default page based on role

**Routing Flow:**
- Login → Auto-redirect to role-appropriate page
- ProtectedRoute wrapper checks authentication
- Admin sees NavigationHeader with links to both Ventas and Gestión
- Non-admin users see single view without navigation header
- `/sunat` route protected and accessible to ventas and admin roles

**Authentication Context:**
- `context/AuthContext` - Manages currentUser state with Firebase (shared across all modules)
- `firebase.js` - Firebase configuration and auth initialization (shared across all modules)
- User object includes: `rol`, `nombre`, `displayName`

### Firebase Configuration

Create `src/config/firebase-config.js` with:
```javascript
export const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "..."
};
```

### Integration with Software-SUNAT

Software-SUNAT is fully integrated as a module within verificador-frontend:
- **Location**: `src/pages/Sunat/` directory
- **Route**: `/sunat` (e.g., `operaciones-peru.web.app/sunat`)
- **Authentication**: Shared Firebase auth from parent app
- **Deployment**: Single build process, no separate compilation needed

**Implementation:**
- `Dashboard.jsx` includes a "Software SUNAT" button that navigates to `/sunat` route
- React Router handles `/sunat` route in `App.jsx`
- `SunatPage.jsx` wraps `Sunat/App.jsx` component
- Shared `AuthContext` and `firebase.js` for authentication
- All SUNAT components and utilities located in `src/pages/Sunat/`

### Deployment

Simplified single-app deployment to Firebase Hosting:

```bash
# Option 1: Automated deployment script (Windows)
cd verificador-frontend
.\deploy.ps1

# Option 2: Automated deployment script (Linux/Mac)
cd verificador-frontend
chmod +x deploy.sh
./deploy.sh

# Option 3: Manual deployment
cd verificador-frontend
npm run build
firebase deploy --only hosting
```

**Note**: Software-SUNAT frontend is now integrated into verificador-frontend and compiles automatically during the build process. No separate build step required.

See `.firebaserc`, `firebase.json`, and `DEPLOY.md` for detailed configuration and deployment instructions.

---

## 3. gcp-microservicios (GCP Microservices)

### Purpose
Event-driven microservices architecture for processing financial operations: parsing emails, fetching data from Cavali (Peru's securities clearing house), uploading documents to Google Drive, sending notifications via Gmail/Trello.

### Architecture Pattern

**Orchestrator-driven sequential workflow:**
1. **orquestador-service** - Central orchestrator (FastAPI)
2. **parser-service** - Parses email data (direct HTTP call)
3. **cavali-service** - Fetches Cavali data (direct HTTP call, fault-tolerant)
4. **drive-service** - Uploads to Google Drive (Pub/Sub parallel)
5. **gmail-service** - Sends email notifications (direct HTTP call)
6. **trello-service** - Creates Trello cards (direct HTTP call)
7. **excel-service** - Updates Google Sheets (Pub/Sub)

### Key Commands

Each microservice follows the same pattern:

```bash
cd gcp-microservicios/<service-name>

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Build Docker image
docker build -t <service-name>:latest .

# Deploy to GCP Cloud Run (example)
gcloud run deploy <service-name> \
  --image gcr.io/PROJECT_ID/<service-name>:latest \
  --platform managed \
  --region us-central1
```

### Orchestrator Architecture

The orchestrator follows a modular architecture (see `orquestador-service/ARCHITECTURE.md`):

```
orquestador-service/
├── main.py                      # FastAPI app + routing
├── core/
│   ├── config.py               # Environment variables
│   └── dependencies.py         # Auth & DB dependencies
├── services/
│   ├── operation_service.py    # Core operation processing
│   ├── microservice_client.py  # HTTP clients for all services
│   └── notification_service.py # Gmail/Trello notifications
├── routers/
│   ├── operations.py           # /operations/* endpoints
│   ├── dashboard.py            # /api/operaciones/* endpoints
│   ├── gestiones.py            # /api/gestiones/* endpoints
│   └── users.py                # /api/users/* endpoints
├── database.py                  # Database connection
├── repository.py               # Data access layer
└── models.py                   # SQLAlchemy ORM models
```

**Main Orchestrator Endpoints:**
- `POST /operations/submit` - Submit new operation
- `GET /operations/status/{id}` - Check operation status
- `POST /operations/pubsub-aggregator` - Drive aggregator callback
- `GET /api/operaciones` - List operations (for dashboard)
- `GET /api/gestiones/operaciones` - Operations queue (for gestiones)
- `POST /api/operaciones/{id}/gestiones` - Add management action
- `POST /api/operaciones/{id}/adelanto-express` - Express advance

**Processing Flow:**
1. Frontend submits operation → `/operations/submit`
2. Orchestrator calls Parser (HTTP) → returns structured data
3. Orchestrator calls Cavali (HTTP, fault-tolerant) → fetches additional data
4. Orchestrator publishes to Drive (Pub/Sub) → runs in parallel
5. Drive service processes → publishes aggregator message
6. Orchestrator aggregator endpoint finalizes operation
7. Orchestrator sends notifications (Gmail/Trello) if configured

### Service Dependencies

All services use FastAPI + Uvicorn. Additional dependencies:

- **parser-service**: lxml (HTML parsing), google-cloud-storage
- **cavali-service**: requests, sqlalchemy, google-cloud-storage
- **drive-service**: google-api-python-client, google-auth-oauthlib
- **gmail-service**: google-api-python-client, pandas, openpyxl, PyPDF2, google-generativeai
- **trello-service**: requests (Trello API client)
- **excel-service**: gspread, google-auth-oauthlib
- **orquestador-service**: sqlalchemy, cloud-sql-python-connector, firebase-admin

### Google Cloud Setup

**Service Accounts:**
- Most services require `service_account.json` for Google Cloud authentication
- Place service account JSON files in respective service directories
- Never commit service account files to git (already in .gitignore)

**Gmail/Drive OAuth:**
- `ztoken/` directory contains script to generate OAuth tokens
- Run `generar_token.py` to create `token.json` for Gmail/Drive access
- Copy `token.json` to gmail-service/ and drive-service/

**Pub/Sub Topics:**
Services communicate via Pub/Sub topics (configured in each service's .env)

### Environment Configuration

Each microservice has its own `.env` file. Common variables:

```env
# All services
PORT=8080                        # Service port
PROJECT_ID=your-gcp-project      # GCP project ID

# Services with Pub/Sub
PUBSUB_TOPIC=topic-name          # Pub/Sub topic to publish
PUBSUB_SUBSCRIPTION=sub-name     # Pub/Sub subscription to listen

# Orchestrator (additional)
DATABASE_URL=postgresql+pg8000://user:pass@host/db
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
PARSER_SERVICE_URL=https://parser-service-url
CAVALI_SERVICE_URL=https://cavali-service-url
GMAIL_SERVICE_URL=https://gmail-service-url
TRELLO_SERVICE_URL=https://trello-service-url
```

### Local Development

Run orchestrator with dependencies:

```bash
# Terminal 1: Orchestrator
cd gcp-microservicios/orquestador-service
python main.py

# Terminal 2: Parser (if testing locally)
cd gcp-microservicios/parser-service
python main.py

# Terminal 3: Drive (if testing locally)
cd gcp-microservicios/drive-service
python main.py
```

For full local testing, all services must be running or configured to use deployed GCP endpoints.

---

## Common Patterns Across Projects

### Python Projects (Software-SUNAT scripts, gcp-microservicios)
- Always activate virtual environment before running
- Use `.env` files for configuration (never commit)
- FastAPI services follow pattern: `main.py` → `uvicorn main:app --reload`
- Service accounts and OAuth tokens never committed to git

### React Projects (Software-SUNAT/frontend, verificador-frontend)
- Vite for dev server and builds
- TailwindCSS for styling
- Default dev server: `http://localhost:5173`
- API base URLs configured in component files (update for production)

### Database Access
- **Software-SUNAT**: PostgreSQL via SQLAlchemy ORM
- **gcp-microservicios**: Cloud SQL via cloud-sql-python-connector

### Authentication
- **Software-SUNAT**: No auth (internal tool)
- **verificador-frontend**: Firebase Authentication with role-based access
- **gcp-microservicios**: Firebase Admin SDK for token verification

---

## Important Notes

### Software-SUNAT
- Scripts process periods sequentially to avoid SUNAT API rate limits
- Current month data is always deleted and re-inserted (no updates)
- Token timeouts: 30s auth, 60s polling, 500s downloads
- Backend is completely independent from extraction scripts
- Frontend requires backend running on port 8000 by default

### verificador-frontend
- Role enforcement happens client-side (Firebase auth)
- Navigation header only visible to admin users
- Each role has specific default redirect path
- Uses Firebase Hosting for deployment

### gcp-microservicios
- Orchestrator follows sequential HTTP + parallel Pub/Sub pattern
- Cavali service is fault-tolerant (failures don't stop workflow)
- Drive service runs in parallel via Pub/Sub for performance
- Notifications (Gmail/Trello) are fire-and-forget
- main_legacy.py kept as rollback option in orchestrator

### Troubleshooting

**Software-SUNAT:**
- Check `periodos_fallidos` table for failed downloads
- Verify SUNAT credentials in CRM-SUNAT/.env
- Ensure PostgreSQL is running and accessible
- Check CORS config in backend/main.py matches frontend URL

**verificador-frontend:**
- Verify Firebase config in src/config/firebase-config.js
- Check user roles in Firebase Authentication users
- Ensure backend services (orchestrator) are accessible

**gcp-microservicios:**
- Check service account permissions in GCP console
- Verify Pub/Sub topics exist and subscriptions are active
- Check Cloud Run logs for service errors
- Ensure environment variables are correctly set in Cloud Run
