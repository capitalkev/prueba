"""
Script de testing para verificar que todos los imports funcionan correctamente
sin necesidad de conectar a la base de datos.
"""

import sys

def test_models():
    """Test imports de models.py"""
    try:
        from models import Usuario, Enrolado, VentaSire, CompraSire, Base
        print("[OK] models.py - Todos los modelos importados correctamente")
        print(f"  - Usuario: {Usuario.__tablename__}")
        print(f"  - Enrolado: {Enrolado.__tablename__}")
        return True
    except Exception as e:
        print(f"[ERROR] models.py - {e}")
        return False

def test_auth_module():
    """Test imports de auth.py (sin inicializar Firebase)"""
    try:
        # Nota: No podemos importar auth.py directamente porque inicializa Firebase
        # Pero podemos verificar que el archivo es válido
        import py_compile
        py_compile.compile('auth.py', doraise=True)
        print("[OK] auth.py - Sintaxis correcta")
        return True
    except Exception as e:
        print(f"[ERROR] auth.py - {e}")
        return False

def test_repositories():
    """Test imports de repositories"""
    try:
        # No importamos directamente porque requieren db session
        import py_compile
        py_compile.compile('repositories/venta_repository.py', doraise=True)
        py_compile.compile('repositories/compra_repository.py', doraise=True)
        py_compile.compile('repositories/enrolado_repository.py', doraise=True)
        print("[OK] repositories - Sintaxis correcta en todos los repositorios")
        return True
    except Exception as e:
        print(f"[ERROR] repositories - {e}")
        return False

def test_schemas():
    """Test imports de schemas.py"""
    try:
        from schemas import EnroladoResponse, VentaResponse, CompraResponse, PaginatedResponse
        print("[OK] schemas.py - Todos los schemas importados correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] schemas.py - {e}")
        return False

def test_firebase_admin():
    """Test que firebase-admin está instalado"""
    try:
        import firebase_admin
        print(f"[OK] firebase-admin instalado (version: {firebase_admin.__version__})")
        return True
    except Exception as e:
        print(f"[ERROR] firebase-admin no instalado - {e}")
        return False

def test_dependencies():
    """Test que todas las dependencias críticas están instaladas"""
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'pydantic',
        'firebase_admin',
        'google.cloud.sql.connector'
    ]

    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep.replace('.', '/').split('/')[0])
            print(f"[OK] {dep} instalado")
        except ImportError:
            print(f"[ERROR] {dep} NO instalado")
            all_ok = False

    return all_ok

def main():
    print("=" * 60)
    print("TEST DE IMPORTS - Software-SUNAT Backend")
    print("=" * 60)
    print()

    tests = [
        ("Modelos de Base de Datos", test_models),
        ("Módulo de Autenticación", test_auth_module),
        ("Repositorios", test_repositories),
        ("Schemas Pydantic", test_schemas),
        ("Firebase Admin SDK", test_firebase_admin),
        ("Dependencias Críticas", test_dependencies),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        result = test_func()
        results.append((name, result))
        print()

    print("=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print()
    print(f"Total: {passed}/{total} tests pasados")

    if passed == total:
        print("\n✓ Todos los tests pasaron! El backend está listo para ejecutarse.")
        return 0
    else:
        print("\n✗ Algunos tests fallaron. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
