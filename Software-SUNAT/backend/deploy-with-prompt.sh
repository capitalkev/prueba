#!/bin/bash

# Script de deployment con prompt seguro para password
# Uso: ./deploy-with-prompt.sh

set -e

echo "============================================"
echo "   DEPLOYMENT - Software-SUNAT Backend"
echo "============================================"
echo ""
echo "Este script desplegará el backend con el nuevo sistema de roles."
echo ""

# Pedir password de forma segura
echo -n "Ingresa el password de PostgreSQL: "
read -s DB_PASSWORD
echo ""
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ ERROR: Password no puede estar vacío"
    exit 1
fi

echo "✅ Password recibido. Iniciando deployment..."
echo ""

# Ejecutar deployment con el password
export DB_PASSWORD
./deploy-to-cloud-run.sh

echo ""
echo "============================================"
echo "   DEPLOYMENT COMPLETADO"
echo "============================================"
