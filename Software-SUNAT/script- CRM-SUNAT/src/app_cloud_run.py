# -*- coding: utf-8 -*-
"""
FastAPI application para Cloud Run - CRM SUNAT
Ejecuta el proceso de actualización mensual cuando se invoca el endpoint.
Diseñado para ser llamado por Cloud Scheduler cada hora.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from typing import Dict
import time
from sqlalchemy import text  # <--- CORRECCIÓN 1: Importar text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="CRM SUNAT - Actualizador Mensual",
    description="API para actualizar registros SIRE de SUNAT automáticamente",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Endpoint raíz para health check."""
    return {
        "status": "ok",
        "service": "CRM SUNAT - Actualizador Mensual",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": {
            "/": "Información del servicio",
            "/actualizar": "POST/GET - Ejecutar actualización",
            "/health": "Health check",
            "/info": "Información de configuración"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint para Cloud Run."""
    try:
        # Verificar conexión a base de datos
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # <--- CORRECCIÓN 2: Usar text("SELECT 1")
        db.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


def ejecutar_actualizacion() -> Dict:
    """
    Ejecuta el proceso de actualización mensual.
    Esta función ejecuta la lógica de main_ultimo_mes.py pero solo para el mes actual.

    Returns:
        Dict con el resultado de la ejecución
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from database import SessionLocal
    from models import Enrolado
    from main_ultimo_mes import procesar_enrolado

    logger.info("=" * 80)
    logger.info("INICIANDO ACTUALIZACIÓN MENSUAL AUTOMÁTICA")
    logger.info("=" * 80)

    inicio = time.time()

    # Obtener periodo actual
    periodo_actual = datetime.now().strftime("%Y%m")
    logger.info(f"Periodo a procesar: {periodo_actual}")

    # Obtener todos los enrolados (tanto pendientes como completos)
    db = SessionLocal()
    try:
        enrolados = db.query(Enrolado).all()

        if not enrolados:
            logger.warning("No hay enrolados en la base de datos")
            return {
                "status": "warning",
                "message": "No hay enrolados para procesar",
                "periodo": periodo_actual,
                "enrolados_procesados": 0,
                "exitosos": 0,
                "fallidos": 0
            }

        logger.info(f"Se procesarán {len(enrolados)} enrolado(s) para el periodo {periodo_actual}")

    finally:
        db.close()

    # Procesar todos los enrolados en paralelo
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))
    exitosos = 0
    fallidos = 0
    errores = []

    logger.info(f"Procesando con {MAX_WORKERS} workers en paralelo...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_enrolado = {
            executor.submit(procesar_enrolado, enrolado, periodo_actual): enrolado
            for enrolado in enrolados
        }

        for future in as_completed(future_to_enrolado):
            enrolado = future_to_enrolado[future]
            try:
                future.result()
                exitosos += 1
                logger.info(f"✅ Completado: {enrolado.ruc}")
            except Exception as exc:
                fallidos += 1
                error_msg = f"Error en {enrolado.ruc}: {str(exc)}"
                logger.error(f"❌ {error_msg}")
                errores.append(error_msg)

    duracion = time.time() - inicio

    resultado = {
        "status": "success" if fallidos == 0 else "partial",
        "message": "Actualización completada",
        "periodo": periodo_actual,
        "enrolados_procesados": len(enrolados),
        "exitosos": exitosos,
        "fallidos": fallidos,
        "duracion_segundos": round(duracion, 2),
        "timestamp": datetime.now().isoformat()
    }

    if errores:
        resultado["errores"] = errores

    logger.info("=" * 80)
    logger.info(f"ACTUALIZACIÓN COMPLETADA - Exitosos: {exitosos}/{len(enrolados)}")
    logger.info("=" * 80)

    return resultado


@app.post("/actualizar")
async def actualizar_post():
    """
    Endpoint POST para ejecutar la actualización mensual.
    Cloud Scheduler llamará a este endpoint cada hora.

    Returns:
        JSON con el resultado de la ejecución
    """
    logger.info("Recibida solicitud POST de actualización")

    try:
        resultado = ejecutar_actualizacion()
        return JSONResponse(status_code=200, content=resultado)

    except Exception as e:
        logger.error(f"Error durante la actualización: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/actualizar")
async def actualizar_get():
    """
    Endpoint GET para ejecutar actualización (para pruebas desde navegador).
    """
    logger.info("Recibida solicitud GET de actualización")

    try:
        resultado = ejecutar_actualizacion()
        return JSONResponse(status_code=200, content=resultado)

    except Exception as e:
        logger.error(f"Error durante la actualización: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/info")
async def info():
    """Información sobre la configuración actual."""
    from database import SessionLocal
    from models import Enrolado

    try:
        db = SessionLocal()
        total_enrolados = db.query(Enrolado).count()
        enrolados_completos = db.query(Enrolado).filter(Enrolado.estado == "completo").count()
        enrolados_pendientes = db.query(Enrolado).filter(Enrolado.estado == "pendiente").count()
        db.close()

        return {
            "service": "CRM SUNAT - Actualizador Mensual",
            "version": "1.0.0",
            "database": "connected",
            "total_enrolados": total_enrolados,
            "enrolados_completos": enrolados_completos,
            "enrolados_pendientes": enrolados_pendientes,
            "max_workers": os.getenv("MAX_WORKERS", "3"),
            "periodo_actual": datetime.now().strftime("%Y%m"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Iniciando servidor FastAPI en puerto {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )