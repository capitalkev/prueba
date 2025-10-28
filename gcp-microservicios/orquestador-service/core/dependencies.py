from fastapi import HTTPException, Header
from firebase_admin import auth

# Firebase se inicializa en main.py

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
