-- Migración: Agregar columnas estado1 y estado2 a la tabla ventas_sire
-- Fecha: 2025-11-06
-- Descripción:
--   estado1: Gestión principal de la factura (Sin gestión, Gestionando, Ganada, Perdida)
--   estado2: Motivo de pérdida cuando estado1 = 'Perdida'

-- Agregar columna estado1
ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado1 VARCHAR(20) DEFAULT 'Sin gestión';

-- Agregar columna estado2 (motivo de pérdida)
ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado2 VARCHAR(50) DEFAULT NULL;

-- Agregar comentarios a las columnas
COMMENT ON COLUMN ventas_sire.estado1 IS 'Estado de gestión de la factura: Sin gestión, Gestionando, Ganada, Perdida';
COMMENT ON COLUMN ventas_sire.estado2 IS 'Motivo de pérdida cuando estado1 = Perdida: Por Tasa, Por Riesgo, Deudor no califica, Cliente no interesado, Competencia, Otro';

-- Crear índice para mejorar consultas por estado
CREATE INDEX IF NOT EXISTS idx_ventas_estado1 ON ventas_sire(estado1);

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
