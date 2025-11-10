# Prompt para Migración: Endpoint /api/users/analysts a Clean Architecture + AWS Cognito

## Contexto del Proyecto

Estoy migrando un sistema de operaciones financieras de Firebase Auth a **AWS Cognito** y refactorizando hacia **Clean Architecture**.

### Arquitectura Actual (Semi-Modular)

```
gcp-microservicios/orquestador-service/
├── main.py                      # FastAPI app principal
├── core/
│   ├── config.py               # Variables de entorno
│   └── dependencies.py         # Auth Firebase & DB dependencies
├── routers/                     # Presentation layer
│   ├── operations.py
│   ├── dashboard.py
│   ├── gestiones.py
│   └── users.py               # ← Endpoint actual aquí
├── services/                    # Business logic
│   ├── operation_service.py
│   ├── microservice_client.py
│   └── notification_service.py
├── repository.py               # Data access layer (Repository Pattern)
├── models.py                   # SQLAlchemy ORM models
└── database.py                 # Database connection

```

### Stack Tecnológico
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL (Cloud SQL)
- **Auth Actual**: Firebase Admin SDK
- **Auth Nueva**: AWS Cognito
- **Patrón**: Repository Pattern + Service Layer

---

## Código Actual a Migrar

### 1. Autenticación Firebase (core/dependencies.py)

```python
from fastapi import HTTPException, Header
from firebase_admin import auth

async def get_current_user(authorization: str = Header(None)):
    """Dependency para autenticación Firebase"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")

    token = authorization.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token["email"],
            "name": decoded_token.get("name", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")
```

### 2. Endpoint Actual (routers/users.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.dependencies import get_current_user
from database import get_db
from repository import OperationRepository
import models

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/analysts")
async def get_analysts(
    user: dict = Depends(get_current_user),  # ← Firebase auth
    db: Session = Depends(get_db)
):
    """Obtiene lista de analistas disponibles"""
    try:
        # ⚠️ PROBLEMA: Retorna TODOS los usuarios, no solo analistas
        usuarios = db.query(models.Usuario).all()

        analysts = [
            {
                "email": usuario.email,
                "nombre": usuario.nombre,
                "ultimo_ingreso": usuario.ultimo_ingreso.isoformat() if usuario.ultimo_ingreso else None
            }
            for usuario in usuarios
        ]

        return {"analysts": analysts}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Modelo Usuario (models.py)

```python
class Usuario(Base):
    __tablename__ = "usuarios"
    email = Column(String(255), primary_key=True, index=True)
    nombre = Column(String(255))
    ultimo_ingreso = Column(DateTime(timezone=True), server_default=func.now())
    rol = Column(String(50), nullable=False, default='ventas')  # ← Campo 'rol'
```

### 4. Repository Actual (repository.py - fragmento relevante)

```python
class OperationRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_and_get_last_login(self, email: str, name: str) -> Optional[datetime]:
        now = datetime.now(timezone.utc)
        usuario = self.db.query(Usuario).filter(Usuario.email == email).first()
        if usuario:
            previous_login = usuario.ultimo_ingreso
            usuario.ultimo_ingreso = now
        else:
            previous_login = None
            usuario = Usuario(email=email, nombre=name, ultimo_ingreso=now)
            self.db.add(usuario)
        self.db.commit()
        return previous_login
```

---

## Objetivo de la Migración

Necesito refactorizar el endpoint `/api/users/analysts` siguiendo **Clean Architecture** con estas características:

### Requisitos Funcionales:
1. ✅ **Autenticación con AWS Cognito** (reemplazar Firebase)
2. ✅ **Filtrar solo usuarios con roles**: `gestion` y `admin`
3. ✅ **Validación de permisos**: Solo usuarios con roles `admin` o `gestion` pueden consultar la lista
4. ✅ **Retornar**: email, nombre, ultimo_ingreso

### Requisitos Arquitecturales:
1. ✅ **Clean Architecture** con capas bien definidas:
   - **Domain**: Entities + Repository Interfaces
   - **Application**: Use Cases (business logic)
   - **Infrastructure**: Repository implementations + Cognito Auth
   - **Presentation**: FastAPI routers

2. ✅ **Inyección de dependencias** usando FastAPI Depends
3. ✅ **Separación de responsabilidades**
4. ✅ **Testeable y mantenible**

---

## Estructura Objetivo (Clean Architecture)

```
gcp-microservicios/orquestador-service/
├── domain/                          # ← NUEVO
│   ├── entities/
│   │   └── user.py                 # User entity
│   └── repositories/
│       └── user_repository.py      # IUserRepository (interface)
│
├── application/                     # ← NUEVO
│   └── use_cases/
│       └── get_analysts_use_case.py
│
├── infrastructure/                  # ← NUEVO
│   ├── auth/
│   │   └── cognito_auth.py        # AWS Cognito authentication
│   └── repositories/
│       └── user_repository_impl.py # PostgreSQL implementation
│
├── presentation/                    # ← Renombrar 'routers/'
│   └── api/
│       └── users.py               # Endpoint refactorizado
│
├── core/
│   ├── config.py
│   └── dependencies.py            # ← Actualizar con Cognito
│
├── database.py                     # Sin cambios
├── models.py                       # Sin cambios (ORM)
└── main.py                         # Actualizar imports

```

---

## Información de AWS Cognito

### Configuración (añadir a .env):
```env
AWS_REGION=us-east-1
AWS_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
AWS_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Validación de Token Cognito (referencia):
```python
import boto3
from jose import jwt, JWTError
from fastapi import HTTPException

# Cognito verifica tokens JWT usando las claves públicas (JWKS)
# URL: https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
```

---

## Tareas a Realizar

### Fase 1: Domain Layer
1. Crear `domain/entities/user.py` con la entidad User
2. Crear `domain/repositories/user_repository.py` con la interfaz IUserRepository

### Fase 2: Application Layer
3. Crear `application/use_cases/get_analysts_use_case.py`
   - Validar permisos del usuario solicitante
   - Obtener usuarios con roles 'gestion' y 'admin'
   - Retornar lista formateada

### Fase 3: Infrastructure Layer
4. Crear `infrastructure/auth/cognito_auth.py`
   - Implementar `get_current_user_cognito()` dependency
   - Validar tokens JWT de Cognito
   - Extraer claims (email, sub, custom:role, etc.)

5. Crear `infrastructure/repositories/user_repository_impl.py`
   - Implementar IUserRepository usando SQLAlchemy
   - Método: `get_users_by_roles(roles: List[str])`

### Fase 4: Presentation Layer
6. Actualizar `routers/users.py` (o mover a `presentation/api/users.py`)
   - Usar `get_current_user_cognito` en vez de Firebase
   - Inyectar GetAnalystsUseCase
   - Endpoint limpio solo para routing

### Fase 5: Integración
7. Actualizar `core/dependencies.py`
   - Agregar factory para GetAnalystsUseCase
   - Configurar inyección de dependencias

8. Actualizar `main.py`
   - Importar nuevos routers si se movieron
   - Remover dependencias de Firebase

---

## Preguntas para Claude

Por favor genera el código completo siguiendo esta arquitectura, considerando:

1. **¿Cómo mapeas los roles de Cognito?**
   - ¿Los roles vienen en custom attributes (`custom:role`)?
   - ¿O en grupos de Cognito?

2. **¿Necesitas crear nuevas tablas o usar la tabla `usuarios` existente?**
   - La tabla tiene campo `rol` (ventas, gestion, admin)
   - Puede ser que Cognito tenga su propia gestión de roles

3. **¿El endpoint debe ser síncrono o asíncrono?**
   - Preferencia: async/await para escalabilidad

4. **¿Formato de respuesta?**
   - Mantener formato actual: `{"analysts": [...]}`
   - O cambiar a Clean Architecture response DTOs

---

## Ejemplo de Uso Esperado

```bash
# Request
GET /api/users/analysts
Authorization: Bearer <cognito-jwt-token>

# Response (exitoso)
{
  "analysts": [
    {
      "email": "analista1@empresa.com",
      "nombre": "Juan Pérez",
      "ultimo_ingreso": "2025-01-10T15:30:00Z"
    },
    {
      "email": "admin@empresa.com",
      "nombre": "María González",
      "ultimo_ingreso": "2025-01-10T14:20:00Z"
    }
  ]
}

# Response (sin permisos)
{
  "detail": "No tiene permisos para acceder a esta información"
}
```

---

## Restricciones y Convenciones

1. **Python 3.10+** con type hints
2. **FastAPI** para routing y dependency injection
3. **Pydantic v2** para validación de datos
4. **SQLAlchemy 2.0** (models.py ya existente)
5. **Logging** estructurado con `logging` module
6. **Exception handling** apropiado en cada capa
7. **Docstrings** en español para funciones públicas

---

## Notas Adicionales

- **NO elimines** código existente hasta confirmar que la migración funciona
- **Mantén retrocompatibilidad** si otros servicios dependen del endpoint actual
- **Considera** crear un directorio `legacy/` para código antiguo
- **Testing**: Considera que necesitaremos unit tests para los use cases

---

## Pregunta Final

Con toda esta información, ¿puedes generar:

1. La estructura completa de carpetas y archivos
2. El código para cada archivo nuevo
3. Las modificaciones necesarias en archivos existentes
4. Un README con instrucciones de deployment

**¿Necesitas alguna aclaración antes de comenzar?**
