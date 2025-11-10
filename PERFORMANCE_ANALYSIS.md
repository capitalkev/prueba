# Análisis de Performance - Módulo SUNAT
**Fecha:** 2025-11-10
**Analista:** Claude (Ingeniero de Datos + Backend Specialist)

## Resumen Ejecutivo

El módulo SUNAT presenta **problemas críticos de performance** que afectan significativamente la experiencia del usuario cuando se manejan grandes volúmenes de datos (100k+ facturas). Los problemas principales son:

- **Backend:** Queries SQL ineficientes, índices faltantes, patrón N+1, agregaciones sin optimizar
- **Frontend:** Carga masiva de datos, falta de memoización, re-renders excesivos, sin virtualización

Con las optimizaciones propuestas, se espera una mejora de **6-10x en velocidad de carga** y **20-40x menos datos transferidos**.

---

## PARTE 1: BACKEND - Análisis SQL y Base de Datos

### Problemas Críticos Identificados

#### 1. N+1 Query Pattern (CRÍTICO - Impacto: 2-5 segundos)

**Ubicación:** `Software-SUNAT/backend/repositories/venta_repository.py:305-383`

**Problema:**
```python
# ACTUAL: Loop en Python ejecuta N queries
enrolados = query.all()  # Query 1: SELECT * FROM enrolados
for enrolado in enrolados:
    ventas = self.db.query(VentaElectronica).filter(
        VentaElectronica.ruc == enrolado.ruc  # Query 2, 3, 4, ... N
    ).all()
```

Con 50 enrolados = 1 + 50 = **51 queries separadas**
Tiempo total: 1ms + (50 × 100ms) = **5 segundos**

**Solución:**
```python
# OPTIMIZADO: Un solo query con JOIN + GROUP BY
query = session.query(
    Enrolado.id,
    Enrolado.ruc,
    func.json_agg(
        func.json_build_object(
            'id', VentaElectronica.id,
            'amount', VentaElectronica.total_cp,
            # ... otros campos
        )
    ).label('invoices')
).outerjoin(VentaElectronica, VentaElectronica.ruc == Enrolado.ruc)\
 .group_by(Enrolado.id, Enrolado.ruc)\
 .all()
```

**Mejora esperada:** 5 segundos → 200ms (**25x más rápido**)

---

#### 2. COUNT() Innecesario en Paginación (CRÍTICO - Impacto: 100-200ms)

**Ubicación:** `Software-SUNAT/backend/repositories/venta_repository.py:169`

**Problema:**
```python
total = query.count()  # Full table scan de 100k registros
results = query.offset(offset).limit(page_size).all()
```

PostgreSQL ejecuta `SELECT COUNT(*) FROM ... WHERE ...` completo antes de retornar 20 resultados.

**Soluciones propuestas:**

**Opción A - Window Function:**
```sql
SELECT *, COUNT(*) OVER() as total_count
FROM ventas_sire
WHERE periodo = '202510'
LIMIT 20 OFFSET 0;
```

**Opción B - Estimación con pg_stats:**
```python
# Usar estadísticas de PostgreSQL para estimación rápida
if page == 1:
    # Solo contar en primera página
    total = query.count()
else:
    # Usar estimación o valor cacheado
    total = estimated_total
```

**Mejora esperada:** 100-200ms reducidos por request

---

#### 3. Índices Compuestos Faltantes (CRÍTICO - Impacto: 50-300ms)

**Ubicación:** `Software-SUNAT/backend/models.py`

**Índices actuales:**
```python
Index("idx_ventas_ruc_periodo", "ruc", "periodo"),
Index("idx_ventas_cliente", "nro_doc_identidad"),
Index("idx_ventas_fecha", "fecha_emision"),
Index("idx_ventas_estado1", "estado1"),
```

**Índices FALTANTES críticos:**

```sql
-- 1. Para /api/metricas - agrupa por moneda en período específico
CREATE INDEX idx_ventas_periodo_moneda
ON ventas_sire(periodo, moneda)
WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%';

-- 2. Para filtros combinados más comunes
CREATE INDEX idx_ventas_ruc_periodo_moneda
ON ventas_sire(ruc, periodo, moneda);

-- 3. Para búsqueda de usuarios autorizados
CREATE INDEX idx_enrolados_email
ON enrolados(email);

-- 4. Para notas de crédito (tipo_cp_doc = '7')
CREATE INDEX idx_ventas_tipo_nro_ruc
ON ventas_sire(tipo_cp_doc, nro_cp_inicial, ruc)
WHERE tipo_cp_doc = '7';

-- 5. Para filtros por estado
CREATE INDEX idx_ventas_ruc_estado1
ON ventas_sire(ruc, estado1);
```

**Mejora esperada:** 50-300ms por query

---

#### 4. Subquery de Notas de Crédito (ALTO - Impacto: 50-200ms)

**Ubicación:** `Software-SUNAT/backend/repositories/venta_repository.py:55-78`

**Problema:**
El subquery se ejecuta SIEMPRE, incluso cuando:
- Solo el 10% de facturas tienen notas de crédito
- Usa `regexp_replace()` sin índice
- Hace SUM() de todas las notas

```python
nc_subquery = self.db.query(...).filter(
    VentaElectronica.tipo_cp_doc == '7'
).group_by(...).subquery()

# Luego LEFT JOIN en TODAS las facturas
query = query.outerjoin(nc_subquery, ...)
```

**Solución:**
Condicionar el JOIN solo cuando se necesita información de NC:

```python
if include_nota_credito_info:
    nc_subquery = ...
    query = query.outerjoin(nc_subquery, ...)
```

O mejor: Calcular NC en frontend solo para facturas que la tienen.

**Mejora esperada:** 50-200ms por query

---

#### 5. Agregaciones Sin Optimizar (MEDIO - Impacto: 100-300ms)

**Ubicación:** `Software-SUNAT/backend/repositories/venta_repository.py:232-257`

**Problema:**
```python
# GET /api/metricas suma TODAS las facturas del período
results = query.group_by(VentaElectronica.moneda).all()
```

Con 50,000 facturas en el período, PostgreSQL hace:
- Full table scan (si no hay índice en período+moneda)
- SUM() de 50,000 números
- GROUP BY en memoria

**Solución:**
```sql
-- Con índice idx_ventas_periodo_moneda, PostgreSQL puede usar index-only scan
SELECT
    moneda,
    SUM(total_cp) as total,
    COUNT(*) as cantidad
FROM ventas_sire
WHERE periodo = '202510'
  AND tipo_cp_doc != '7'
  AND serie_cdp NOT LIKE 'B%'
GROUP BY moneda;

-- O usar MATERIALIZED VIEW para períodos pasados
CREATE MATERIALIZED VIEW mv_metricas_por_periodo AS
SELECT periodo, moneda, SUM(total_cp) as total, COUNT(*) as cantidad
FROM ventas_sire
WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%'
GROUP BY periodo, moneda;

-- Refresh solo cuando hay datos nuevos
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_por_periodo;
```

**Mejora esperada:** 100-300ms → 10-50ms

---

### Cambios Recomendados en Backend

#### Script SQL de Índices (Implementar INMEDIATAMENTE)

Ver archivo: `Software-SUNAT/backend/migrations/002_add_performance_indexes.sql`

**Tiempo de implementación:** 1-2 horas (creación de índices en producción)

---

#### Refactorización de Queries (Implementar esta semana)

**Prioridad 1:** Eliminar N+1 en `get_clientes_con_facturas_optimizado`
- Archivo: `venta_repository.py:305-383`
- Tiempo: 2-3 horas
- Impacto: **25x mejora**

**Prioridad 2:** Optimizar COUNT() en paginación
- Archivo: `venta_repository.py:169`
- Tiempo: 1 hora
- Impacto: **100-200ms reducidos**

**Prioridad 3:** Condicionar subquery de NC
- Archivo: `venta_repository.py:55-78`
- Tiempo: 30 minutos
- Impacto: **50-200ms reducidos**

---

#### Nuevo Endpoint para Métricas (Implementar esta semana)

**Crear:** `GET /api/metricas/resumen`

```python
@app.get("/api/metricas/resumen")
def get_metricas_resumen(
    fecha_desde: str,
    fecha_hasta: str,
    ruc_empresa: Optional[List[str]] = Query(None),
    moneda: Optional[List[str]] = Query(None),
    usuario_emails: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint optimizado que retorna SOLO métricas agregadas,
    sin retornar 10,000 facturas completas.
    """
    query = db.query(
        VentaElectronica.moneda,
        func.sum(VentaElectronica.total_cp).label('total_facturado'),
        func.sum(case(
            (VentaElectronica.estado1 == 'Ganada', VentaElectronica.total_cp),
            else_=0
        )).label('monto_ganado'),
        func.count(VentaElectronica.id).label('cantidad')
    ).filter(
        VentaElectronica.fecha_emision >= fecha_desde,
        VentaElectronica.fecha_emision <= fecha_hasta,
        # ... otros filtros
    ).group_by(VentaElectronica.moneda)

    results = query.all()

    return {
        currency: {
            "totalFacturado": float(row.total_facturado),
            "montoGanado": float(row.monto_ganado),
            "montoDisponible": float(row.total_facturado - row.monto_ganado),
            "cantidad": row.cantidad
        }
        for row in results
        for currency in [row.moneda]
    }
```

**Respuesta:**
```json
{
  "PEN": {
    "totalFacturado": 1234567.89,
    "montoGanado": 234567.89,
    "montoDisponible": 1000000.00,
    "cantidad": 1523
  },
  "USD": {
    "totalFacturado": 567890.12,
    "montoGanado": 123456.78,
    "montoDisponible": 444433.34,
    "cantidad": 342
  }
}
```

**Mejora:** De transferir 10,000 facturas (10-15 MB) a solo métricas (< 1 KB) = **10000x menos datos**

---

#### Logging en Producción (Implementar cuando sea conveniente)

**Problema:** Print statements en producción
```python
print("🎯 [ENDPOINT] GET /api/ventas recibió:")
```

**Solución:**
```python
import logging

logger = logging.getLogger(__name__)

# En main.py configurar logging:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Cambiar prints por:
logger.debug(f"GET /api/ventas - page: {page}, size: {page_size}")
logger.info(f"Query returned {total} results in {elapsed_time}ms")
```

---

## PARTE 2: FRONTEND - Análisis React y Performance

### Problemas Críticos Identificados

#### 1. Carga de 10,000 Registros para Métricas (CRÍTICO - Impacto: 5-15 MB)

**Ubicación:** `verificador-frontend/src/pages/Sunat/hooks/useSunatData.js:137`

**Problema:**
```javascript
let url = `${API_BASE_URL}/api/ventas?page=1&page_size=10000&fecha_desde=${startDate}&fecha_hasta=${endDate}`;
const response = await fetch(url, ...);
const data = await response.json();
```

Se cargan 10,000 facturas completas solo para calcular 4 métricas:
- Total facturado PEN
- Total facturado USD
- Monto ganado
- Monto disponible

**Solución:**
Usar el nuevo endpoint `/api/metricas/resumen`:

```javascript
// En useSunatData.js - Crear función separada
const fetchMetrics = async () => {
    const url = `${API_BASE_URL}/api/metricas/resumen?fecha_desde=${startDate}&fecha_hasta=${endDate}&rucs_empresa=${selectedClientIds.join(',')}&moneda=${selectedCurrencies.join(',')}&usuario_emails=${selectedUserEmails.join(',')}`;

    const response = await fetch(url, { headers: authHeaders });
    const metrics = await response.json();

    setMetrics(metrics);
};

// Solo llamar fetchMetrics cuando cambien filtros principales
useEffect(() => {
    if (!firebaseUser) return;
    fetchMetrics();
}, [startDate, endDate, selectedClientIds, selectedCurrencies, selectedUserEmails]);
```

**Mejora esperada:** 10-15 MB → < 1 KB transferido (**10000x menos datos**)

---

#### 2. Componentes sin Memoización (CRÍTICO - Impacto: 5-10 re-renders)

**Ubicación:**
- `verificador-frontend/src/pages/Sunat/components/InvoiceTable.jsx`
- `verificador-frontend/src/pages/Sunat/components/GroupedInvoiceTable.jsx`

**Problema:**
Cada cambio en el estado de App causa re-render de TODAS las filas de tabla:
- Seleccionar checkbox → re-render de 100 filas
- Cambiar estado de factura → re-render de 100 filas
- Expandir grupo → re-render de todos los grupos

**Solución:**

```jsx
// Crear InvoiceRow.jsx memoizado
import React from 'react';

const InvoiceRow = React.memo(({
    invoice,
    isSelected,
    onToggleSelection,
    onStatusChange,
    onViewCompany
}) => {
    return (
        <tr className={...}>
            {/* Contenido de la fila */}
        </tr>
    );
}, (prevProps, nextProps) => {
    // Solo re-renderizar si cambian props relevantes
    return (
        prevProps.invoice.id === nextProps.invoice.id &&
        prevProps.isSelected === nextProps.isSelected &&
        prevProps.invoice.status === nextProps.invoice.status &&
        prevProps.invoice.montoNeto === nextProps.invoice.montoNeto
    );
});

export default InvoiceRow;
```

```jsx
// En InvoiceTable.jsx
import InvoiceRow from './InvoiceRow';

{invoices.map(invoice => (
    <InvoiceRow
        key={invoice.key}
        invoice={invoice}
        isSelected={selectedInvoiceKeys.includes(invoice.key)}
        onToggleSelection={onToggleSelection}
        onStatusChange={onStatusChange}
        onViewCompany={onViewCompany}
    />
))}
```

**Mejora esperada:** 5-10 re-renders → 1 re-render (solo la fila afectada)

---

#### 3. Exceso de Dependencias en useSunatData (ALTO - Impacto: 2-3 fetches)

**Ubicación:** `verificador-frontend/src/pages/Sunat/hooks/useSunatData.js:269`

**Problema:**
```javascript
}, [startDate, endDate, currentPage, selectedClientIds, clients.length,
    sortBy, selectedCurrencies, selectedUserEmails, firebaseUser,
    viewMode, users.length]);
```

11 dependencias = 11 oportunidades de re-fetch innecesario

**Ejemplos de fetches innecesarios:**
- Cambiar `viewMode` (grouped ↔ detailed) hace fetch nuevo
- Cambiar `sortBy` hace fetch nuevo (¡debería ordenar en cliente!)
- Cambiar `clients.length` hace fetch (aunque sean los mismos clientes)

**Solución:**

```javascript
// Crear objeto de filtros estable
const filters = useMemo(() => ({
    dateRange: { startDate, endDate },
    clientIds: selectedClientIds,
    currencies: selectedCurrencies,
    userEmails: selectedUserEmails
}), [startDate, endDate, selectedClientIds, selectedCurrencies, selectedUserEmails]);

// Separar fetch de datos vs. transformación
useEffect(() => {
    fetchVentas(filters, currentPage);
}, [filters, currentPage, firebaseUser]);

// Ordenar en cliente, no en servidor
const sortedVentas = useMemo(() => {
    return [...ventas].sort((a, b) => {
        if (sortBy === 'fecha') return new Date(b.fecha_emision) - new Date(a.fecha_emision);
        if (sortBy === 'monto') return b.total_cp - a.total_cp;
        return 0;
    });
}, [ventas, sortBy]);

// viewMode no necesita re-fetch, solo afecta renderizado
```

**Mejora esperada:** 2-3 fetches por acción → 1 fetch solo cuando cambian datos reales

---

#### 4. Sin Virtualización de Tablas (ALTO - Impacto: 100+ nodos DOM)

**Ubicación:** `verificador-frontend/src/pages/Sunat/components/InvoiceTable.jsx`

**Problema:**
Con 100 facturas en pantalla:
- 100 elementos `<tr>` renderizados
- ~20 `<td>` por fila = 2000 nodos DOM
- Solo 10-15 filas son visibles en viewport

**Solución:**

```bash
npm install react-window
```

```jsx
import { FixedSizeList as List } from 'react-window';

const InvoiceTableVirtualized = ({ invoices, ...props }) => {
    const Row = ({ index, style }) => {
        const invoice = invoices[index];
        return (
            <div style={style}>
                <InvoiceRow invoice={invoice} {...props} />
            </div>
        );
    };

    return (
        <List
            height={600}
            itemCount={invoices.length}
            itemSize={50}
            width="100%"
        >
            {Row}
        </List>
    );
};
```

**Mejora esperada:** 2000 nodos DOM → 20 nodos DOM (**100x menos**)

---

#### 5. Transformación de Datos Duplicada (MEDIO - Impacto: CPU)

**Ubicación:** `verificador-frontend/src/pages/Sunat/App.jsx:110-178`

**Problema:**
```javascript
// Transformación 1: para tabla
const invoices = useMemo(() => {
    return ventas.map(venta => {
        // ... 30 líneas de lógica
    });
}, [ventas, invoiceStatuses]);

// Transformación 2: para métricas (casi idéntica)
const allInvoicesTransformed = useMemo(() => {
    return allInvoicesForMetrics.map(venta => {
        // ... 30 líneas de lógica repetida
    });
}, [allInvoicesForMetrics, invoiceStatuses]);
```

**Solución:**

```javascript
// Crear función auxiliar reutilizable
const transformInvoice = useCallback((venta, invoiceStatuses) => {
    const invoiceId = `${venta.serie_cdp || ''}-${venta.nro_cp_inicial || venta.id}`;
    const clientId = venta.ruc;
    const statusKey = `${clientId}-${invoiceId}`;

    let amount = parseFloat(venta.monto_original ?? venta.total_cp ?? 0);
    const notaCreditoMonto = parseFloat(venta.nota_credito_monto ?? 0);
    const montoNeto = amount - notaCreditoMonto;

    return {
        id: invoiceId,
        ventaId: venta.id,
        clientId,
        clientName: venta.razon_social || venta.ruc,
        amount,
        netAmount: montoNeto,
        currency: venta.moneda || 'PEN',
        emissionDate: venta.fecha_emision,
        debtor: venta.apellidos_nombres_razon_social || '-',
        debtorRuc: venta.nro_doc_identidad || '-',
        status: invoiceStatuses[statusKey] || venta.estado1 || 'Sin gestión',
        estado2: venta.estado2,
        usuarioNombre: venta.usuario_nombre,
        usuarioEmail: venta.usuario_email
    };
}, []);

// Usar la misma función para ambos
const invoices = useMemo(
    () => ventas.map(v => transformInvoice(v, invoiceStatuses)),
    [ventas, invoiceStatuses, transformInvoice]
);

const allInvoicesTransformed = useMemo(
    () => allInvoicesForMetrics.map(v => transformInvoice(v, invoiceStatuses)),
    [allInvoicesForMetrics, invoiceStatuses, transformInvoice]
);
```

**Mejora esperada:** Código más limpio, menos CPU usage

---

### Cambios Recomendados en Frontend

#### Implementación Inmediata (< 1 hora cada uno)

1. **Memoizar InvoiceRow:**
   - Crear `InvoiceRow.jsx` con `React.memo`
   - Tiempo: 30 minutos
   - Impacto: **5-10x menos re-renders**

2. **Memoizar GroupedTableRow:**
   - Aplicar `React.memo` a `GroupedTableRow`
   - Tiempo: 30 minutos
   - Impacto: **5x menos re-renders en vista agrupada**

3. **Consumir nuevo endpoint de métricas:**
   - Cambiar fetch de 10k registros a `/api/metricas/resumen`
   - Tiempo: 1 hora (requiere backend primero)
   - Impacto: **10-15 MB → 1 KB transferido**

---

#### Implementación Esta Semana (2-4 horas cada uno)

4. **Implementar virtualización:**
   - Instalar react-window
   - Refactorizar InvoiceTable para virtualización
   - Tiempo: 3 horas
   - Impacto: **100x menos nodos DOM**

5. **Reducir dependencias en useSunatData:**
   - Separar filtros de datos vs. opciones de vista
   - Mover sorting a cliente
   - Tiempo: 2 horas
   - Impacto: **2-3x menos fetches**

6. **Unificar transformación de datos:**
   - Crear función `transformInvoice` reutilizable
   - Tiempo: 1 hora
   - Impacto: **Código más limpio, menos bugs**

---

#### Mejoras Futuras (Opcional)

7. **Infinite Scroll:**
   - Implementar carga progresiva en scroll
   - Tiempo: 4 horas
   - Impacto: **Mejor UX con grandes datasets**

8. **Cache de métricas:**
   - Cachear métricas por 5 minutos en localStorage
   - Tiempo: 1 hora
   - Impacto: **Carga instantánea al volver a página**

---

## PARTE 3: Plan de Implementación

### Fase 1: Quick Wins (Hoy - 2-3 horas total)

**BACKEND:**
1. ✅ Crear archivo SQL con índices críticos
2. ✅ Ejecutar índices en base de datos de desarrollo
3. ✅ Crear endpoint `/api/metricas/resumen`
4. ✅ Probar endpoint con Postman/Thunder Client

**FRONTEND:**
1. ✅ Crear `InvoiceRow.jsx` memoizado
2. ✅ Memoizar `GroupedTableRow`
3. ✅ Probar mejora visual

**Mejora esperada después de Fase 1:** +40-50% velocidad

---

### Fase 2: Optimizaciones Backend (Esta semana - 4-6 horas)

**BACKEND:**
1. ✅ Eliminar N+1 en `get_clientes_con_facturas`
2. ✅ Optimizar COUNT() en paginación
3. ✅ Condicionar subquery de NC
4. ✅ Reemplazar prints por logging
5. ✅ Deploy a producción

**Mejora esperada después de Fase 2:** +60-70% velocidad backend

---

### Fase 3: Optimizaciones Frontend (Próxima semana - 4-6 horas)

**FRONTEND:**
1. ✅ Consumir `/api/metricas/resumen`
2. ✅ Implementar virtualización con react-window
3. ✅ Reducir dependencias en useSunatData
4. ✅ Unificar transformación de datos
5. ✅ Deploy a Firebase Hosting

**Mejora esperada después de Fase 3:** +80-90% velocidad frontend

---

### Fase 4: Mejoras Adicionales (Futuro)

**BACKEND:**
- Implementar caché con Redis
- Crear MATERIALIZED VIEWs para períodos pasados
- Cursor-based pagination

**FRONTEND:**
- Infinite scroll
- Cache en localStorage
- Progressive loading de detalles

---

## PARTE 4: Métricas de Éxito

### Antes de Optimizaciones:

| Métrica | Valor Actual |
|---------|-------------|
| Tiempo carga inicial | 2-5 segundos |
| Tiempo cambio filtros | 1-3 segundos |
| Datos transferidos (métricas) | 10-15 MB |
| Queries SQL por request | 1-51 queries |
| Nodos DOM renderizados | 2000+ |
| Re-renders por acción | 5-10 |

### Después de TODAS las Optimizaciones:

| Métrica | Valor Objetivo |
|---------|---------------|
| Tiempo carga inicial | 300-800ms ⚡ |
| Tiempo cambio filtros | 200-500ms ⚡ |
| Datos transferidos (métricas) | < 1 KB ⚡ |
| Queries SQL por request | 1-2 queries ⚡ |
| Nodos DOM renderizados | 20-40 ⚡ |
| Re-renders por acción | 1-2 ⚡ |

### Mejora Total Esperada:

- **Backend:** 6-10x más rápido
- **Frontend:** 5-10x más rápido
- **Datos transferidos:** 20-40x menos
- **Experiencia usuario:** Transformación radical

---

## PARTE 5: Archivos a Modificar

### Backend (Software-SUNAT/backend/)

```
backend/
├── migrations/
│   └── 002_add_performance_indexes.sql ← CREAR
├── repositories/
│   └── venta_repository.py ← MODIFICAR (líneas 55, 169, 305)
├── main.py ← MODIFICAR (añadir endpoint /api/metricas/resumen)
└── models.py ← REVISAR (confirmar índices)
```

### Frontend (verificador-frontend/src/pages/Sunat/)

```
Sunat/
├── hooks/
│   └── useSunatData.js ← MODIFICAR (reducir dependencias, nuevo endpoint)
├── components/
│   ├── InvoiceRow.jsx ← CREAR (memoizado)
│   ├── InvoiceTable.jsx ← MODIFICAR (usar InvoiceRow)
│   ├── GroupedTableRow.jsx ← MODIFICAR (añadir React.memo)
│   └── GroupedInvoiceTable.jsx ← MODIFICAR (usar GroupedTableRow memoizado)
└── App.jsx ← MODIFICAR (unificar transformación, consumir nuevo endpoint)
```

---

## Conclusión

El módulo SUNAT tiene problemas de performance clásicos pero todos son solucionables:

1. **Backend:** Queries SQL ineficientes típicas de ORMs sin optimización
2. **Frontend:** Re-renders excesivos típicos de React sin memoización

Con el plan propuesto, en **2-3 semanas** (10-15 horas de trabajo) se puede lograr:
- ✅ 6-10x mejora en velocidad
- ✅ 20-40x menos datos transferidos
- ✅ Soporte para 10-20x más usuarios concurrentes
- ✅ Experiencia de usuario transformada

**Prioridad #1:** Crear índices SQL (1-2 horas, impacto inmediato)
**Prioridad #2:** Endpoint de métricas + memoización frontend (2-3 horas, impacto masivo)

---

**Generado por:** Claude (Sonnet 4.5)
**Fecha:** 2025-11-10
