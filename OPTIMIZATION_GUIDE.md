# Guía de Implementación de Optimizaciones - SUNAT Module

Esta guía contiene código específico y paso a paso para implementar las optimizaciones críticas identificadas en `PERFORMANCE_ANALYSIS.md`.

---

## Tabla de Contenidos

1. [Backend Optimizations](#backend-optimizations)
   - [Eliminar N+1 Query](#1-eliminar-n1-query-en-get_clientes_con_facturas)
   - [Optimizar COUNT()](#2-optimizar-count-en-paginación)
   - [Crear Endpoint de Métricas](#3-crear-endpoint-apimetricasresumen)
   - [Condicionar Subquery NC](#4-condicionar-subquery-de-notas-de-crédito)
   - [Implementar Logging](#5-implementar-logging-profesional)

2. [Frontend Optimizations](#frontend-optimizations)
   - [Memoizar InvoiceRow](#1-memoizar-invoicerow)
   - [Memoizar GroupedTableRow](#2-memoizar-groupedtablerow)
   - [Consumir Endpoint de Métricas](#3-consumir-endpoint-de-métricas)
   - [Implementar Virtualización](#4-implementar-virtualización)
   - [Reducir Dependencias Hook](#5-reducir-dependencias-en-usesunatdata)

3. [Testing y Validación](#testing-y-validación)

---

## BACKEND OPTIMIZATIONS

### 1. Eliminar N+1 Query en get_clientes_con_facturas

**Problema:** 50 enrolados = 51 queries separadas = 5 segundos

**Archivo:** `Software-SUNAT/backend/repositories/venta_repository.py`

**Líneas a modificar:** 305-383

#### Código ACTUAL (MALO):

```python
def get_clientes_con_facturas_optimizado(
    self,
    periodo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    sort_by: Optional[str] = None,
    usuario_emails: Optional[List[str]] = None,
    moneda: Optional[List[str]] = None,
    authorized_rucs: Optional[List[str]] = None
):
    # Query 1: SELECT * FROM enrolados
    enrolados_query = self.db.query(Enrolado)

    if authorized_rucs:
        enrolados_query = enrolados_query.filter(Enrolado.ruc.in_(authorized_rucs))

    enrolados = enrolados_query.all()  # ← QUERY 1

    result = []
    for enrolado in enrolados:  # ← LOOP EN PYTHON
        # Query 2, 3, 4, 5... N
        ventas_query = self.db.query(VentaElectronica).filter(
            VentaElectronica.ruc == enrolado.ruc  # ← UNA QUERY POR ENROLADO
        )

        # Filtros...
        ventas = ventas_query.all()  # ← QUERY SEPARADA

        # Transformación...
        result.append({
            "id": enrolado.id,
            "ruc": enrolado.ruc,
            "name": enrolado.ruc,
            "available_invoices": [...]
        })

    return result
```

#### Código OPTIMIZADO (BUENO):

```python
from sqlalchemy import func, case, and_
from sqlalchemy.dialects.postgresql import aggregate_order_by

def get_clientes_con_facturas_optimizado(
    self,
    periodo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    sort_by: Optional[str] = None,
    usuario_emails: Optional[List[str]] = None,
    moneda: Optional[List[str]] = None,
    authorized_rucs: Optional[List[str]] = None
):
    """
    Versión optimizada que usa SQL JOIN + GROUP BY
    en lugar de loop en Python.

    Mejora: 5 segundos → 200ms (25x más rápido)
    """

    # Construir JSON de factura en SQL
    invoice_json = func.json_build_object(
        'id', VentaElectronica.id,
        'amount', case(
            (VentaElectronica.tipo_cambio > 0,
             VentaElectronica.total_cp / VentaElectronica.tipo_cambio),
            else_=VentaElectronica.total_cp
        ),
        'debtor', VentaElectronica.apellidos_nombres_razon_social,
        'emissionDate', VentaElectronica.fecha_emision,
        'ruc_cliente', VentaElectronica.nro_doc_identidad,
        'moneda', VentaElectronica.moneda,
        'invoice_number', func.concat(
            VentaElectronica.serie_cdp,
            '-',
            VentaElectronica.nro_cp_inicial
        )
    )

    # Subquery para facturas con filtros
    ventas_subquery = self.db.query(
        VentaElectronica.ruc.label('venta_ruc'),
        invoice_json.label('invoice_data'),
        VentaElectronica.fecha_emision.label('fecha')
    ).filter(
        VentaElectronica.tipo_cp_doc != '7',
        ~VentaElectronica.serie_cdp.like('B%')
    )

    # Aplicar filtros de período
    if periodo:
        ventas_subquery = ventas_subquery.filter(VentaElectronica.periodo == periodo)
    elif fecha_desde and fecha_hasta:
        ventas_subquery = ventas_subquery.filter(
            VentaElectronica.fecha_emision >= fecha_desde,
            VentaElectronica.fecha_emision <= fecha_hasta
        )

    # Filtro por moneda
    if moneda and len(moneda) > 0:
        ventas_subquery = ventas_subquery.filter(VentaElectronica.moneda.in_(moneda))

    ventas_subquery = ventas_subquery.subquery()

    # Query principal con JOIN y GROUP BY
    query = self.db.query(
        Enrolado.id,
        Enrolado.ruc,
        Enrolado.ruc.label('name'),
        func.coalesce(
            func.json_agg(
                ventas_subquery.c.invoice_data
            ).filter(ventas_subquery.c.invoice_data.isnot(None)),
            func.cast('[]', type_=JSON)
        ).label('available_invoices')
    ).outerjoin(
        ventas_subquery,
        Enrolado.ruc == ventas_subquery.c.venta_ruc
    )

    # Filtro por RUCs autorizados
    if authorized_rucs:
        query = query.filter(Enrolado.ruc.in_(authorized_rucs))

    # Filtro por usuarios (si aplica)
    if usuario_emails and len(usuario_emails) > 0:
        query = query.join(Usuario, Enrolado.email == Usuario.email)\
                     .filter(Usuario.email.in_(usuario_emails))

    # Group by para agregar facturas
    query = query.group_by(Enrolado.id, Enrolado.ruc)

    # Ejecutar query
    results = query.all()

    # Transformar a diccionarios
    return [
        {
            "id": row.id,
            "ruc": row.ruc,
            "name": row.name,
            "available_invoices": row.available_invoices
        }
        for row in results
    ]
```

#### Ventajas de la versión optimizada:

1. ✅ **1 query en lugar de N+1** - De 51 queries a 1 query
2. ✅ **PostgreSQL hace el trabajo pesado** - Más eficiente que Python
3. ✅ **Usa índices** - idx_ventas_ruc_periodo aprovechado
4. ✅ **json_agg en SQL** - Construcción de JSON nativa
5. ✅ **Mantiene la misma respuesta** - Compatible con frontend

#### Testing:

```python
# Test comparativo
import time

# Versión antigua
start = time.time()
result_old = repo.get_clientes_con_facturas_optimizado_OLD(...)
time_old = time.time() - start
print(f"Versión antigua: {time_old:.2f}s, {len(result_old)} resultados")

# Versión nueva
start = time.time()
result_new = repo.get_clientes_con_facturas_optimizado(...)
time_new = time.time() - start
print(f"Versión nueva: {time_new:.2f}s, {len(result_new)} resultados")

print(f"Mejora: {time_old/time_new:.1f}x más rápido")
```

---

### 2. Optimizar COUNT() en Paginación

**Problema:** COUNT(*) evalúa todas las filas antes de LIMIT

**Archivo:** `Software-SUNAT/backend/repositories/venta_repository.py`

**Líneas a modificar:** 169

#### Código ACTUAL (MALO):

```python
# Línea 169
total = query.count()  # ← Full table scan
results = query.offset(offset).limit(page_size).all()
```

#### Opción 1: Window Function (RECOMENDADO)

```python
from sqlalchemy import func, over

def get_ventas_paginadas(...):
    # ... código anterior ...

    # Añadir window function para count
    query_with_count = query.add_columns(
        func.count().over().label('total_count')
    )

    # Aplicar paginación
    results = query_with_count.offset(offset).limit(page_size).all()

    if results:
        # Total count está en cada fila
        total = results[0].total_count
        # Extraer solo los objetos VentaElectronica
        ventas = [row[0] for row in results]
    else:
        total = 0
        ventas = []

    return ventas, total
```

#### Opción 2: Estimación con Caché (MÁS SIMPLE)

```python
# Añadir al inicio del archivo
from functools import lru_cache

class VentaRepository:
    def __init__(self, db):
        self.db = db
        self._count_cache = {}  # Cache de conteos por filtros

    def get_ventas_paginadas(...):
        # ... código anterior ...

        # Generar clave de cache basada en filtros
        cache_key = f"{periodo}:{ruc_empresa}:{fecha_desde}:{fecha_hasta}:{moneda}"

        # Solo contar si:
        # 1. Es la primera página
        # 2. No está en cache
        # 3. Cache expiró (> 5 minutos)
        if page == 1:
            total = query.count()
            self._count_cache[cache_key] = {
                'count': total,
                'timestamp': time.time()
            }
        else:
            # Usar cache si existe y es reciente
            cached = self._count_cache.get(cache_key)
            if cached and (time.time() - cached['timestamp']) < 300:  # 5 min
                total = cached['count']
            else:
                total = query.count()
                self._count_cache[cache_key] = {
                    'count': total,
                    'timestamp': time.time()
                }

        results = query.offset(offset).limit(page_size).all()

        return results, total
```

#### Opción 3: Límite en COUNT (PRAGMÁTICA)

```python
def get_ventas_paginadas(...):
    # ... código anterior ...

    # Si hay muchos resultados, estimamos en lugar de contar todo
    # Primero intentamos contar hasta 10,000
    count_limit = 10000

    # Usar LIMIT en la subquery de COUNT
    total_query = query.limit(count_limit + 1)
    total_results = total_query.count()

    if total_results > count_limit:
        # Si hay más de 10k, retornamos "10,000+"
        total = count_limit
        has_more = True
    else:
        total = total_results
        has_more = False

    results = query.offset(offset).limit(page_size).all()

    return results, total, has_more
```

**Recomendación:** Usar Opción 2 (Caché) por simplicidad y compatibilidad.

---

### 3. Crear Endpoint /api/metricas/resumen

**Archivo:** `Software-SUNAT/backend/main.py`

**Dónde añadir:** Después de la línea 539 (después de `get_metricas_periodo`)

#### Código Nuevo:

```python
from pydantic import BaseModel
from typing import Dict

class MetricaMoneda(BaseModel):
    totalFacturado: float
    montoGanado: float
    montoDisponible: float
    cantidad: int

class MetricasResumenResponse(BaseModel):
    PEN: Optional[MetricaMoneda] = None
    USD: Optional[MetricaMoneda] = None

@app.get("/api/metricas/resumen", response_model=MetricasResumenResponse)
def get_metricas_resumen(
    fecha_desde: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_hasta: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    rucs_empresa: Optional[List[str]] = Query(None, description="Lista de RUCs a filtrar"),
    moneda: Optional[List[str]] = Query(None, description="Lista de monedas (PEN, USD)"),
    usuario_emails: Optional[List[str]] = Query(None, description="Lista de emails de usuarios"),
    firebaseUser: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Endpoint optimizado que retorna SOLO métricas agregadas.

    Ventajas vs GET /api/ventas?page_size=10000:
    - 10,000 registros (10-15 MB) → Solo métricas (< 1 KB)
    - Query optimizado con índices
    - Respuesta instantánea

    Ejemplo de uso:
    GET /api/metricas/resumen?fecha_desde=2025-10-01&fecha_hasta=2025-10-31&rucs_empresa=12345678901

    Respuesta:
    {
      "PEN": {
        "totalFacturado": 1234567.89,
        "montoGanado": 234567.89,
        "montoDisponible": 1000000.00,
        "cantidad": 1523
      },
      "USD": { ... }
    }
    """

    print(f"🎯 [ENDPOINT] GET /api/metricas/resumen")
    print(f"   Filtros: desde={fecha_desde}, hasta={fecha_hasta}")
    print(f"   RUCs: {rucs_empresa}")
    print(f"   Monedas: {moneda}")
    print(f"   Usuarios: {usuario_emails}")

    try:
        # Obtener RUCs autorizados para el usuario
        authorized_rucs = get_rucs_autorizados_por_usuario(db, firebaseUser.get("email"))

        if not authorized_rucs:
            raise HTTPException(status_code=403, detail="Usuario sin empresas autorizadas")

        # Query base
        query = db.query(
            VentaElectronica.moneda,
            func.sum(VentaElectronica.total_cp).label('total_facturado'),
            func.sum(
                case(
                    (VentaElectronica.estado1 == 'Ganada', VentaElectronica.total_cp),
                    else_=0
                )
            ).label('monto_ganado'),
            func.count(VentaElectronica.id).label('cantidad')
        ).filter(
            VentaElectronica.fecha_emision >= fecha_desde,
            VentaElectronica.fecha_emision <= fecha_hasta,
            VentaElectronica.tipo_cp_doc != '7',  # Excluir NC
            ~VentaElectronica.serie_cdp.like('B%'),  # Excluir boletas
            VentaElectronica.ruc.in_(authorized_rucs)
        )

        # Filtros opcionales
        if rucs_empresa and len(rucs_empresa) > 0:
            query = query.filter(VentaElectronica.ruc.in_(rucs_empresa))

        if moneda and len(moneda) > 0:
            query = query.filter(VentaElectronica.moneda.in_(moneda))

        # Filtro por usuarios
        if usuario_emails and len(usuario_emails) > 0:
            query = query.join(Enrolado, VentaElectronica.ruc == Enrolado.ruc)\
                         .join(Usuario, Enrolado.email == Usuario.email)\
                         .filter(Usuario.email.in_(usuario_emails))

        # Group by moneda
        query = query.group_by(VentaElectronica.moneda)

        # Ejecutar
        results = query.all()

        # Transformar a diccionario
        metricas = {}
        for row in results:
            total_facturado = float(row.total_facturado or 0)
            monto_ganado = float(row.monto_ganado or 0)

            metricas[row.moneda] = {
                "totalFacturado": total_facturado,
                "montoGanado": monto_ganado,
                "montoDisponible": total_facturado - monto_ganado,
                "cantidad": row.cantidad
            }

        print(f"✅ [SUCCESS] Métricas calculadas: {list(metricas.keys())}")

        return metricas

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] get_metricas_resumen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {str(e)}")
```

#### Testing del Endpoint:

```bash
# Usando curl
curl -X GET "http://localhost:8000/api/metricas/resumen?fecha_desde=2025-10-01&fecha_hasta=2025-10-31" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"

# Esperado:
# {
#   "PEN": {
#     "totalFacturado": 1234567.89,
#     "montoGanado": 234567.89,
#     "montoDisponible": 1000000.00,
#     "cantidad": 1523
#   }
# }
```

---

### 4. Condicionar Subquery de Notas de Crédito

**Archivo:** `Software-SUNAT/backend/repositories/venta_repository.py`

**Líneas a modificar:** 55-78

#### Código ACTUAL (MALO):

```python
# Líneas 55-78
nc_subquery = self.db.query(
    VentaElectronica.ruc.label('nc_ruc'),
    func.regexp_replace(...).label('nc_nro_modificado'),
    # ... grupo por 3 columnas
).filter(
    VentaElectronica.tipo_cp_doc == '7'
).group_by(...).subquery()

# Siempre hace LEFT JOIN
query = query.outerjoin(
    nc_subquery,
    and_(...) # condiciones complejas
)
```

#### Código OPTIMIZADO (BUENO):

```python
def get_ventas_paginadas(
    self,
    # ... parámetros ...
    include_nota_credito: bool = False  # ← Nuevo parámetro
):
    """
    ...

    Nuevo parámetro:
    - include_nota_credito: Si True, incluye información de NC (más lento).
                           Si False, omite NC (más rápido).
    """

    # Query base
    query = self.db.query(VentaElectronica)

    # Usuario info (si aplica)
    if usuario_emails:
        query = query.outerjoin(Enrolado, ...)\
                     .outerjoin(Usuario, ...)

    # Solo incluir NC si se solicita explícitamente
    if include_nota_credito:
        # Subquery optimizado de NC
        nc_subquery = self.db.query(
            VentaElectronica.ruc.label('nc_ruc'),
            VentaElectronica.nro_cp_inicial.label('nc_nro_cp'),  # Usar nro directo
            VentaElectronica.nro_doc_identidad.label('nc_cliente'),
            func.sum(
                case(
                    (VentaElectronica.tipo_cambio > 0,
                     VentaElectronica.total_cp / VentaElectronica.tipo_cambio),
                    else_=VentaElectronica.total_cp
                )
            ).label('nc_total')
        ).filter(
            VentaElectronica.tipo_cp_doc == '7'
        ).group_by(
            VentaElectronica.ruc,
            VentaElectronica.nro_cp_inicial,  # Más simple que regexp_replace
            VentaElectronica.nro_doc_identidad
        ).subquery()

        # JOIN condicional
        query = query.outerjoin(
            nc_subquery,
            and_(
                VentaElectronica.ruc == nc_subquery.c.nc_ruc,
                VentaElectronica.nro_cp_inicial == nc_subquery.c.nc_nro_cp,
                VentaElectronica.nro_doc_identidad == nc_subquery.c.nc_cliente
            )
        )

        # Añadir columna NC a SELECT
        query = query.add_columns(
            func.coalesce(nc_subquery.c.nc_total, 0).label('nota_credito_monto')
        )

    # Resto de filtros...
    # ...

    return query
```

#### Modificar endpoint para usar nuevo parámetro:

```python
# En main.py

@app.get("/api/ventas", response_model=PaginatedResponse[VentaResponse])
def get_ventas(
    # ... parámetros existentes ...
    include_nc: bool = Query(False, description="Incluir info de notas de crédito"),
    # ...
):
    """
    ...
    Nuevo parámetro opcional:
    - include_nc: Si true, incluye montos de NC (más lento pero completo)
    """

    ventas, total = venta_repo.get_ventas_paginadas(
        # ... parámetros ...
        include_nota_credito=include_nc  # ← Pasar parámetro
    )

    # ...
```

**Ventajas:**
- Frontend puede solicitar NC solo cuando necesita
- Queries sin NC son 50-200ms más rápidas
- Mantiene compatibilidad (default False)

---

### 5. Implementar Logging Profesional

**Archivos a modificar:**
- `Software-SUNAT/backend/main.py`
- `Software-SUNAT/backend/repositories/venta_repository.py`

#### Paso 1: Configurar logging en main.py

```python
# Al inicio de main.py (después de imports)
import logging
from logging.handlers import RotatingFileHandler
import os

# Configurar logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/sunat_backend.log")

# Crear directorio de logs si no existe
os.makedirs("logs", exist_ok=True)

# Configurar formato
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Rotar logs cada 10 MB, mantener 5 archivos
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        ),
        # También mostrar en consola
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# En startup de FastAPI
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 SUNAT Backend iniciado")
    logger.info(f"📝 Logs en: {LOG_FILE}")
    logger.info(f"📊 Nivel de log: {LOG_LEVEL}")
```

#### Paso 2: Reemplazar prints en endpoints

```python
# ANTES:
print("🎯 [ENDPOINT] GET /api/ventas recibió:")
print(f"  page: {page}, page_size: {page_size}")

# DESPUÉS:
logger.debug(f"GET /api/ventas - page={page}, size={page_size}")
logger.info(f"GET /api/ventas - filtros: ruc={ruc_empresa}, periodo={periodo}")

# Para errores:
# ANTES:
print(f"❌ Error al obtener ventas: {str(e)}")

# DESPUÉS:
logger.error(f"Error en GET /api/ventas: {str(e)}", exc_info=True)
```

#### Paso 3: Logging en repository

```python
# En venta_repository.py
import logging

logger = logging.getLogger(__name__)

class VentaRepository:
    def get_ventas_paginadas(self, ...):
        logger.debug(f"Query ventas: page={page}, filters=[ruc={ruc_empresa}, periodo={periodo}]")

        # ... query ...

        logger.info(f"Ventas encontradas: {total} total, retornando {len(results)}")

        return results, total
```

#### Configuración de niveles de log:

```python
# .env
LOG_LEVEL=DEBUG  # Desarrollo: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/sunat_backend.log

# Producción
LOG_LEVEL=INFO
LOG_FILE=/var/log/sunat/backend.log
```

---

## FRONTEND OPTIMIZATIONS

### 1. Memoizar InvoiceRow

**Archivo:** Crear nuevo archivo `verificador-frontend/src/pages/Sunat/components/InvoiceRow.jsx`

#### Código Completo:

```jsx
import React from 'react';
import { formatCurrency } from '../utils/formatters';

const InvoiceRow = React.memo(({
    invoice,
    isSelected,
    onToggleSelection,
    onStatusChange,
    onViewCompany,
    selectMode,
    showCheckboxes
}) => {
    const rowClassName = `
        border-b hover:bg-gray-50 transition-colors cursor-pointer
        ${isSelected ? 'bg-blue-50' : ''}
    `;

    const statusColor = {
        'Nueva Oportunidad': 'bg-blue-100 text-blue-800',
        'Contactado': 'bg-yellow-100 text-yellow-800',
        'Negociación': 'bg-purple-100 text-purple-800',
        'Ganada': 'bg-green-100 text-green-800',
        'Perdida': 'bg-red-100 text-red-800',
        'Sin gestión': 'bg-gray-100 text-gray-600'
    }[invoice.status] || 'bg-gray-100 text-gray-600';

    return (
        <tr className={rowClassName}>
            {showCheckboxes && (
                <td className="py-3 px-2 text-center">
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => onToggleSelection(invoice.key)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2"
                    />
                </td>
            )}

            <td className="py-3 px-4">
                <button
                    onClick={() => onViewCompany(invoice.clientId)}
                    className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-sm"
                >
                    {invoice.clientName}
                </button>
                <div className="text-xs text-gray-500">RUC: {invoice.clientId}</div>
            </td>

            <td className="py-3 px-4 text-sm">{invoice.id}</td>

            <td className="py-3 px-4 text-sm">
                <div>{invoice.debtor}</div>
                <div className="text-xs text-gray-500">RUC: {invoice.debtorRuc}</div>
            </td>

            <td className="py-3 px-4 text-sm text-right font-medium">
                <div>{formatCurrency(invoice.amount, invoice.currency)}</div>
                {invoice.amount !== invoice.netAmount && (
                    <div className="text-xs text-gray-500">
                        Neto: {formatCurrency(invoice.netAmount, invoice.currency)}
                    </div>
                )}
            </td>

            <td className="py-3 px-4 text-sm text-center">{invoice.currency}</td>

            <td className="py-3 px-4 text-sm">{invoice.emissionDate}</td>

            <td className="py-3 px-4">
                <select
                    value={invoice.status}
                    onChange={(e) => onStatusChange(invoice.ventaId, e.target.value, invoice.estado2)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor}`}
                >
                    <option value="Nueva Oportunidad">Nueva Oportunidad</option>
                    <option value="Contactado">Contactado</option>
                    <option value="Negociación">Negociación</option>
                    <option value="Ganada">Ganada</option>
                    <option value="Perdida">Perdida</option>
                    <option value="Sin gestión">Sin gestión</option>
                </select>
            </td>

            <td className="py-3 px-4 text-sm">
                {invoice.usuarioNombre || invoice.usuarioEmail || '-'}
            </td>
        </tr>
    );
}, (prevProps, nextProps) => {
    // Custom comparison - solo re-render si cambianpropiedades relevantes
    return (
        prevProps.invoice.ventaId === nextProps.invoice.ventaId &&
        prevProps.invoice.status === nextProps.invoice.status &&
        prevProps.invoice.amount === nextProps.invoice.amount &&
        prevProps.invoice.netAmount === nextProps.invoice.netAmount &&
        prevProps.isSelected === nextProps.isSelected &&
        prevProps.selectMode === nextProps.selectMode
    );
});

InvoiceRow.displayName = 'InvoiceRow';

export default InvoiceRow;
```

#### Modificar InvoiceTable.jsx para usar InvoiceRow:

```jsx
// En InvoiceTable.jsx
import InvoiceRow from './InvoiceRow';

const InvoiceTable = ({ invoices, ...props }) => {
    return (
        <table className="min-w-full bg-white">
            <thead>
                {/* ... thead code ... */}
            </thead>
            <tbody>
                {invoices.map(invoice => (
                    <InvoiceRow
                        key={invoice.key}
                        invoice={invoice}
                        isSelected={props.selectedInvoiceKeys.includes(invoice.key)}
                        onToggleSelection={props.onToggleSelection}
                        onStatusChange={props.onStatusChange}
                        onViewCompany={props.onViewCompany}
                        selectMode={props.selectMode}
                        showCheckboxes={props.showCheckboxes}
                    />
                ))}
            </tbody>
        </table>
    );
};

export default InvoiceTable;
```

**Mejora esperada:** 5-10 re-renders → 1 re-render (solo fila afectada)

---

### 2. Memoizar GroupedTableRow

**Archivo:** `verificador-frontend/src/pages/Sunat/components/GroupedTableRow.jsx`

#### Modificar componente existente:

```jsx
// Al inicio del archivo
import React from 'react';

// Al final del archivo, envolver con React.memo
const GroupedTableRow = React.memo(({
    group,
    isExpanded,
    onExpandGroup,
    selectedInvoiceKeys,
    onToggleSelection,
    onStatusChange,
    onSelectAllInGroup,
    onDeselectAllInGroup,
    selectMode,
    showCheckboxes
}) => {
    // ... código existente ...

    return (
        <React.Fragment>
            {/* Fila principal del grupo */}
            <tr className="...">
                {/* ... contenido ... */}
            </tr>

            {/* Filas expandidas */}
            {isExpanded && (
                <tr>
                    <td colSpan="100%">
                        <div className="bg-gray-50 p-4">
                            <table className="min-w-full">
                                <tbody>
                                    {group.invoices.map(invoice => (
                                        <InvoiceRow
                                            key={invoice.key}
                                            invoice={invoice}
                                            isSelected={selectedInvoiceKeys.includes(invoice.key)}
                                            {...otherProps}
                                        />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </td>
                </tr>
            )}
        </React.Fragment>
    );
}, (prevProps, nextProps) => {
    // Solo re-renderizar si:
    // 1. El grupo cambió
    // 2. Se expandió/colapsó
    // 3. Cambió la selección de facturas dentro del grupo

    const prevSelected = prevProps.selectedInvoiceKeys.filter(
        key => prevProps.group.invoices.some(inv => inv.key === key)
    );
    const nextSelected = nextProps.selectedInvoiceKeys.filter(
        key => nextProps.group.invoices.some(inv => inv.key === key)
    );

    return (
        prevProps.group.key === nextProps.group.key &&
        prevProps.isExpanded === nextProps.isExpanded &&
        prevProps.group.invoices.length === nextProps.group.invoices.length &&
        prevProps.group.total === nextProps.group.total &&
        JSON.stringify(prevSelected) === JSON.stringify(nextSelected)
    );
});

GroupedTableRow.displayName = 'GroupedTableRow';

export default GroupedTableRow;
```

**Mejora esperada:** Expandir grupo no causa re-render de otros grupos

---

### 3. Consumir Endpoint de Métricas

**Archivo:** `verificador-frontend/src/pages/Sunat/hooks/useSunatData.js`

#### Modificar hook para usar nuevo endpoint:

```jsx
// Añadir nuevo estado para métricas
const [metrics, setMetrics] = useState({
    PEN: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
    USD: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 }
});
const [metricsLoading, setMetricsLoading] = useState(false);

// ELIMINAR la carga de 10,000 registros:
// ANTES:
// let url = `${API_BASE_URL}/api/ventas?page=1&page_size=10000&...`;

// DESPUÉS - Nueva función separada:
const fetchMetrics = useCallback(async () => {
    if (!firebaseUser || !startDate || !endDate) return;

    setMetricsLoading(true);

    try {
        const token = await firebaseUser.getIdToken();

        // Construir query params
        const params = new URLSearchParams({
            fecha_desde: startDate,
            fecha_hasta: endDate
        });

        // Añadir filtros opcionales
        if (selectedClientIds.length > 0) {
            selectedClientIds.forEach(ruc => params.append('rucs_empresa', ruc));
        }

        if (selectedCurrencies.length > 0) {
            selectedCurrencies.forEach(currency => params.append('moneda', currency));
        }

        if (selectedUserEmails.length > 0) {
            selectedUserEmails.forEach(email => params.append('usuario_emails', email));
        }

        // Llamar al nuevo endpoint
        const url = `${API_BASE_URL}/api/metricas/resumen?${params.toString()}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        // Actualizar métricas
        setMetrics({
            PEN: data.PEN || { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
            USD: data.USD || { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 }
        });

    } catch (error) {
        console.error('Error fetching metrics:', error);
        setMetrics({
            PEN: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 },
            USD: { totalFacturado: 0, montoGanado: 0, montoDisponible: 0, cantidad: 0 }
        });
    } finally {
        setMetricsLoading(false);
    }
}, [firebaseUser, startDate, endDate, selectedClientIds, selectedCurrencies, selectedUserEmails]);

// Ejecutar fetchMetrics cuando cambien filtros
useEffect(() => {
    fetchMetrics();
}, [fetchMetrics]);

// Retornar métricas en el return del hook
return {
    ventas,
    metrics,  // ← Nueva propiedad
    metricsLoading,  // ← Nueva propiedad
    loading,
    error,
    // ... resto
};
```

#### Modificar App.jsx para usar métricas:

```jsx
// En App.jsx
const {
    ventas,
    metrics,  // ← Nuevo
    metricsLoading,  // ← Nuevo
    loading,
    error,
    totalPages,
    lastUpdate
} = useSunatData(...);

// ELIMINAR cálculo manual de métricas:
// const invoices = useMemo(() => { ... }, [allInvoicesForMetrics, ...]);

// Usar directamente metrics
<KPIDashboard
    metrics={metrics}
    loading={metricsLoading}
/>
```

**Mejora esperada:** 10-15 MB → < 1 KB transferido

---

### 4. Implementar Virtualización

**Paso 1:** Instalar react-window

```bash
cd verificador-frontend
npm install react-window
```

**Paso 2:** Crear InvoiceTableVirtualized.jsx

```jsx
import React from 'react';
import { FixedSizeList as List } from 'react-window';
import InvoiceRow from './InvoiceRow';

const InvoiceTableVirtualized = ({
    invoices,
    selectedInvoiceKeys,
    onToggleSelection,
    onStatusChange,
    onViewCompany,
    selectMode,
    showCheckboxes
}) => {
    // Renderizar una fila
    const Row = ({ index, style }) => {
        const invoice = invoices[index];

        return (
            <div style={style}>
                <InvoiceRow
                    invoice={invoice}
                    isSelected={selectedInvoiceKeys.includes(invoice.key)}
                    onToggleSelection={onToggleSelection}
                    onStatusChange={onStatusChange}
                    onViewCompany={onViewCompany}
                    selectMode={selectMode}
                    showCheckboxes={showCheckboxes}
                />
            </div>
        );
    };

    return (
        <div className="border rounded-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gray-100 grid grid-cols-9 gap-4 px-4 py-3 font-semibold text-sm">
                {showCheckboxes && <div>Selección</div>}
                <div>Cliente</div>
                <div>N° Factura</div>
                <div>Deudor</div>
                <div className="text-right">Monto</div>
                <div className="text-center">Moneda</div>
                <div>Fecha Emisión</div>
                <div>Estado</div>
                <div>Usuario</div>
            </div>

            {/* Lista virtualizada */}
            <List
                height={600}  // Altura del viewport
                itemCount={invoices.length}
                itemSize={60}  // Altura de cada fila
                width="100%"
                overscanCount={5}  // Renderizar 5 filas extra arriba/abajo
            >
                {Row}
            </List>
        </div>
    );
};

export default InvoiceTableVirtualized;
```

**Paso 3:** Usar en App.jsx

```jsx
// En App.jsx
import InvoiceTableVirtualized from './components/InvoiceTableVirtualized';

// Dentro del render:
{viewMode === 'detailed' && (
    <InvoiceTableVirtualized
        invoices={invoices}
        selectedInvoiceKeys={selectedInvoiceKeys}
        onToggleSelection={toggleInvoiceSelection}
        onStatusChange={handleStatusChange}
        onViewCompany={handleViewCompany}
        selectMode={selectMode}
        showCheckboxes={true}
    />
)}
```

**Mejora esperada:** 2000 nodos DOM → 20 nodos DOM

---

### 5. Reducir Dependencias en useSunatData

**Archivo:** `verificador-frontend/src/pages/Sunat/hooks/useSunatData.js`

#### Refactorizar dependencias:

```jsx
// ANTES: 11 dependencias
}, [startDate, endDate, currentPage, selectedClientIds, clients.length,
    sortBy, selectedCurrencies, selectedUserEmails, firebaseUser,
    viewMode, users.length]);

// DESPUÉS: Separar en múltiples efectos

// 1. Efecto para datos (solo cuando cambien filtros reales)
const filters = useMemo(() => ({
    dateRange: { startDate, endDate },
    clientIds: selectedClientIds,
    currencies: selectedCurrencies,
    userEmails: selectedUserEmails
}), [startDate, endDate, selectedClientIds, selectedCurrencies, selectedUserEmails]);

useEffect(() => {
    fetchVentas();
}, [filters, currentPage, firebaseUser]);  // Solo 3 dependencias

// 2. Ordenar en cliente (no requiere re-fetch)
const sortedVentas = useMemo(() => {
    if (!ventas) return [];

    const sorted = [...ventas];

    if (sortBy === 'fecha') {
        sorted.sort((a, b) => new Date(b.fecha_emision) - new Date(a.fecha_emision));
    } else if (sortBy === 'monto') {
        sorted.sort((a, b) => b.total_cp - a.total_cp);
    }

    return sorted;
}, [ventas, sortBy]);

// 3. viewMode solo afecta paginación (ajustar page_size localmente)
const displayedVentas = useMemo(() => {
    const pageSize = viewMode === 'grouped' ? 100 : 20;
    // Aquí podrías paginar en cliente si ya tienes los datos
    return sortedVentas;
}, [sortedVentas, viewMode]);
```

**Mejora esperada:** 2-3 fetches por acción → 1 fetch solo cuando sea necesario

---

## TESTING Y VALIDACIÓN

### Backend Testing

#### 1. Test de Performance de Queries

```python
# test_performance.py
import time
from repositories.venta_repository import VentaRepository
from database import SessionLocal

def test_get_ventas_performance():
    db = SessionLocal()
    repo = VentaRepository(db)

    # Test con filtros reales
    start = time.time()
    ventas, total = repo.get_ventas_paginadas(
        page=1,
        page_size=20,
        periodo="202510",
        ruc_empresa=["12345678901"],
        moneda=["PEN"]
    )
    elapsed = time.time() - start

    print(f"✅ Query completada en {elapsed:.2f}s")
    print(f"   Resultados: {len(ventas)} de {total}")

    # Aserciones
    assert elapsed < 1.0, f"Query muy lenta: {elapsed:.2f}s (esperado < 1s)"
    assert len(ventas) <= 20
    assert total >= len(ventas)

if __name__ == "__main__":
    test_get_ventas_performance()
```

#### 2. Test de Endpoint de Métricas

```bash
# Usar httpie o curl
http GET "http://localhost:8000/api/metricas/resumen?fecha_desde=2025-10-01&fecha_hasta=2025-10-31" \
  "Authorization:Bearer YOUR_TOKEN"

# Esperado: < 100ms response time
```

### Frontend Testing

#### 1. Test de Re-renders

```jsx
// Añadir en InvoiceRow.jsx (solo para testing)
const InvoiceRow = React.memo(({ ... }) => {
    console.log(`🔄 Renderizando fila ${invoice.id}`);

    // ... resto del código
}, ...);

// En consola del navegador:
// - Cambiar estado de 1 factura → debería ver solo 1 log
// - Seleccionar checkbox → debería ver solo 1 log
```

#### 2. Test de Virtualización

```jsx
// Verificar en React DevTools:
// - Profiler tab → Record
// - Hacer scroll rápido
// - Stop recording
// - Verificar que solo se renderizan ~20 componentes
```

#### 3. Benchmark de Carga

```javascript
// En useSunatData.js
const fetchMetrics = async () => {
    const startTime = performance.now();

    // ... fetch ...

    const endTime = performance.now();
    console.log(`⏱️ Métricas cargadas en ${(endTime - startTime).toFixed(2)}ms`);
};

// Esperado:
// - Antes: 2000-5000ms (10k registros)
// - Después: 50-200ms (solo métricas)
```

---

## Checklist de Implementación

### Backend (8-10 horas)

- [ ] Ejecutar `002_add_performance_indexes.sql` en PostgreSQL
- [ ] Verificar índices creados con `SELECT * FROM pg_indexes WHERE tablename = 'ventas_sire';`
- [ ] Refactorizar `get_clientes_con_facturas` para eliminar N+1
- [ ] Optimizar COUNT() en paginación (opción de caché)
- [ ] Crear endpoint `/api/metricas/resumen`
- [ ] Condicionar subquery de notas de crédito
- [ ] Configurar logging con RotatingFileHandler
- [ ] Reemplazar todos los prints por logger
- [ ] Testing de performance con queries reales
- [ ] Deploy a producción (staging primero)

### Frontend (6-8 horas)

- [ ] Crear componente `InvoiceRow.jsx` memoizado
- [ ] Modificar `InvoiceTable.jsx` para usar `InvoiceRow`
- [ ] Memoizar `GroupedTableRow` con React.memo
- [ ] Modificar `useSunatData` para llamar `/api/metricas/resumen`
- [ ] Eliminar carga de 10k registros en frontend
- [ ] Modificar `App.jsx` para usar metrics del nuevo endpoint
- [ ] Instalar react-window
- [ ] Crear `InvoiceTableVirtualized.jsx`
- [ ] Integrar virtualización en vista detallada
- [ ] Reducir dependencias en `useSunatData`
- [ ] Testing de re-renders en DevTools
- [ ] Build y deploy a Firebase Hosting

### Validación (2-3 horas)

- [ ] Comparar tiempos antes/después con Network tab
- [ ] Verificar queries SQL con EXPLAIN ANALYZE
- [ ] Test de carga con 50+ usuarios concurrentes
- [ ] Monitoreo de logs de PostgreSQL
- [ ] Verificar métricas de Cloud Run (si aplica)
- [ ] User Acceptance Testing con usuario real
- [ ] Documentar mejoras logradas

---

## Resultado Esperado

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tiempo carga inicial | 2-5s | 300-800ms | **6-10x** |
| Tiempo cambio filtros | 1-3s | 200-500ms | **5-6x** |
| Datos transferidos | 10-20 MB | 100-500 KB | **20-40x** |
| Queries SQL | 1-51 | 1-2 | **25x** |
| Nodos DOM | 2000+ | 20-40 | **50-100x** |
| Re-renders | 5-10 | 1-2 | **5x** |

**Tiempo total de implementación:** 16-21 horas
**ROI:** Muy alto - mejora transformacional en UX

---

Generado por: Claude (Sonnet 4.5)
Fecha: 2025-11-10
