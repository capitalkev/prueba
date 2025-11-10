-- Migración OPTIMIZADA: Agregar columnas estado1 y estado2 sin timeout
-- Estrategia: Agregar columnas como NULL primero (rápido), luego índice
-- El valor por defecto se maneja en la aplicación (modelo SQLAlchemy)

-- Paso 1: Agregar columnas como NULL (operación rápida, no bloquea)
ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado1 VARCHAR(20) DEFAULT NULL;

ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado2 VARCHAR(50) DEFAULT NULL;

-- Paso 2: Crear índice para mejorar consultas
CREATE INDEX IF NOT EXISTS idx_ventas_estado1 ON ventas_sire(estado1);

-- Paso 3: Agregar comentarios
COMMENT ON COLUMN ventas_sire.estado1 IS 'Estado de gestión de la factura: Sin gestión, Gestionando, Ganada, Perdida';
COMMENT ON COLUMN ventas_sire.estado2 IS 'Motivo de pérdida cuando estado1 = Perdida: Por Tasa, Por Riesgo, Deudor no califica, Cliente no interesado, Competencia, Otro';

-- Verificar la creación de las columnas
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'ventas_sire'
AND column_name IN ('estado1', 'estado2')
ORDER BY column_name;

-- NOTA: Los registros existentes tendrán NULL en estado1
-- La aplicación maneja esto mostrando "Sin gestión" cuando estado1 es NULL
-- Los nuevos registros insertados tendrán el valor por defecto del modelo SQLAlchemy
