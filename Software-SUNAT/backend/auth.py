"""
Módulo de autenticación Firebase para el backend de Software-SUNAT.
Proporciona middleware para verificar tokens JWT de Firebase.
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, auth
import logging

from database import get_db
from models import Enrolado, Usuario

# Inicializar Firebase Admin SDK
try:
    if not firebase_admin._apps:
        # Usar Application Default Credentials (funciona en local y GCP)
        firebase_admin.initialize_app(credentials.ApplicationDefault())
    logging.info("Firebase Admin SDK inicializado correctamente")
except Exception as e:
    logging.warning(f"No se pudo inicializar Firebase Admin SDK: {e}")
    logging.warning("La autenticación Firebase no estará disponible")


async def get_current_user_email(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Verifica el token de Firebase y extrae el email del usuario.

    Args:
        authorization: Header Authorization con formato "Bearer <token>"

    Returns:
        str: Email del usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o falta
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token de autorización no proporcionado o inválido"
        )

    try:
        token = authorization.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        email = decoded_token.get('email')

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Token válido pero sin email asociado"
            )

        return email

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token de Firebase inválido o expirado"
        )
    except Exception as e:
        logging.error(f"Error verificando token Firebase: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Error al verificar autenticación: {str(e)}"
        )


def get_or_create_user(user_email: str, user_name: str, db: Session) -> Usuario:
    """
    Obtiene un usuario existente o lo crea automáticamente.

    Args:
        user_email: Email del usuario autenticado
        user_name: Nombre del usuario (de Firebase)
        db: Sesión de base de datos

    Returns:
        Usuario: Objeto Usuario de la base de datos
    """
    usuario = db.query(Usuario).filter(Usuario.email == user_email).first()

    if not usuario:
        # Auto-registrar usuario con rol 'usuario' por defecto
        usuario = Usuario(
            email=user_email,
            nombre=user_name or user_email.split('@')[0],
            rol='usuario'
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        logging.info(f"Nuevo usuario registrado: {user_email} con rol 'usuario'")
    else:
        # Actualizar último ingreso
        from datetime import datetime, timezone
        usuario.ultimo_ingreso = datetime.now(timezone.utc)
        db.commit()
        logging.info(f"Usuario {user_email} autenticado (rol: {usuario.rol})")

    return usuario


def get_authorized_rucs(user_email: str, user_rol: str, db: Session) -> Optional[list[str]]:
    """
    Obtiene la lista de RUCs autorizados para un email dado.
    Si el usuario es admin, retorna None (acceso a todos los RUCs).

    Args:
        user_email: Email del usuario autenticado
        user_rol: Rol del usuario ('admin' o 'usuario')
        db: Sesión de base de datos

    Returns:
        Optional[list[str]]: Lista de RUCs autorizados, o None si es admin (acceso total)
    """
    # Admin ve TODOS los RUCs
    if user_rol == 'admin':
        logging.info(f"Usuario {user_email} es ADMIN - acceso a todos los RUCs")
        return None

    # Usuario normal: filtrar por enrolados.email
    enrolados = db.query(Enrolado).filter(Enrolado.email == user_email).all()

    if not enrolados:
        logging.warning(f"Usuario {user_email} no tiene enrolados asociados")
        return []

    rucs = [enrolado.ruc for enrolado in enrolados]
    logging.info(f"Usuario {user_email} tiene acceso a {len(rucs)} RUCs: {rucs}")

    return rucs


async def get_user_context(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependencia combinada que retorna el contexto completo del usuario:
    - email: Email del usuario autenticado
    - nombre: Nombre del usuario
    - rol: Rol del usuario ('admin' o 'usuario')
    - authorized_rucs: Lista de RUCs a los que tiene acceso (None si es admin)

    Uso en endpoints:
        @app.get("/api/ventas")
        def get_ventas(user_context: dict = Depends(get_user_context)):
            email = user_context["email"]
            rol = user_context["rol"]
            rucs = user_context["authorized_rucs"]  # None si es admin
    """
    # Obtener o crear usuario (con rol)
    # Intentar extraer nombre del token de Firebase
    try:
        from firebase_admin import auth as firebase_auth
        user_record = firebase_auth.get_user_by_email(email)
        user_name = user_record.display_name or email.split('@')[0]
    except Exception:
        user_name = email.split('@')[0]

    usuario = get_or_create_user(email, user_name, db)

    # Obtener RUCs autorizados según rol
    authorized_rucs = get_authorized_rucs(email, usuario.rol, db)

    logging.info(f"✅ Usuario autenticado: {email}, rol: {usuario.rol}, RUCs: {authorized_rucs}")

    return {
        "email": email,
        "nombre": usuario.nombre,
        "rol": usuario.rol,
        "authorized_rucs": authorized_rucs  # None si es admin, lista si es usuario
    }


async def get_optional_user_context(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Dependencia de autenticación OPCIONAL.
    Si hay token, valida y retorna contexto de usuario.
    Si NO hay token, retorna None (acceso público sin restricciones).

    Uso en endpoints públicos:
        @app.get("/api/ventas")
        def get_ventas(user_context: Optional[dict] = Depends(get_optional_user_context)):
            if user_context:
                # Usuario autenticado - aplicar filtros
                authorized_rucs = user_context["authorized_rucs"]
            else:
                # Acceso público - sin filtros (admin implícito)
                authorized_rucs = None
    """
    # Si no hay header de autorización, retornar None (acceso público)
    if not authorization or not authorization.startswith("Bearer "):
        logging.info("Acceso público sin autenticación")
        return None

    try:
        # Validar token y obtener email
        token = authorization.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        email = decoded_token.get('email')

        if not email:
            logging.warning("Token válido pero sin email")
            return None

        # Obtener contexto de usuario
        try:
            from firebase_admin import auth as firebase_auth
            user_record = firebase_auth.get_user_by_email(email)
            user_name = user_record.display_name or email.split('@')[0]
        except Exception:
            user_name = email.split('@')[0]

        usuario = get_or_create_user(email, user_name, db)
        authorized_rucs = get_authorized_rucs(email, usuario.rol, db)

        return {
            "email": email,
            "nombre": usuario.nombre,
            "rol": usuario.rol,
            "authorized_rucs": authorized_rucs
        }

    except Exception as e:
        # Si hay error en validación de token, permitir acceso público
        logging.warning(f"Error al validar token (permitiendo acceso público): {e}")
        return None
