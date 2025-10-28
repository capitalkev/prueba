-- Migración: Crear tabla usuarios para control de acceso basado en roles
-- Fecha: 2025-01-XX
-- Descripción: Agrega tabla usuarios con roles (admin/usuario) para el backend de Software-SUNAT

-- Crear tabla usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    email VARCHAR(255) PRIMARY KEY,
    nombre VARCHAR(255),
    ultimo_ingreso TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rol VARCHAR(50) NOT NULL DEFAULT 'usuario',
    CONSTRAINT check_rol CHECK (rol IN ('admin', 'usuario'))
);

-- Crear índice en rol para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);

-- Comentarios de la tabla
COMMENT ON TABLE usuarios IS 'Usuarios del sistema con control de roles';
COMMENT ON COLUMN usuarios.email IS 'Email del usuario (primary key, vinculado con Firebase Auth)';
COMMENT ON COLUMN usuarios.nombre IS 'Nombre completo del usuario';
COMMENT ON COLUMN usuarios.ultimo_ingreso IS 'Fecha y hora del último ingreso al sistema';
COMMENT ON COLUMN usuarios.rol IS 'Rol del usuario: admin (ve todo) o usuario (ve solo RUCs asignados)';

-- Insertar usuario admin por defecto (CAMBIAR EMAIL SEGÚN NECESIDAD)
-- Descomenta y modifica la siguiente línea para crear tu primer admin:
-- INSERT INTO usuarios (email, nombre, rol)
-- VALUES ('admin@empresa.com', 'Administrador', 'admin')
-- ON CONFLICT (email) DO NOTHING;

-- Verificar creación
SELECT 'Tabla usuarios creada exitosamente' AS status;
SELECT * FROM usuarios;
