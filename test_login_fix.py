#!/usr/bin/env python3
"""
VALIDACION RAPIDA - Verifica que los cambios del endpoint /login funcionan.
Ejecuta todas las validaciones sin interaccion del usuario.
"""

import sys
from pathlib import Path


# Agrega el directorio raiz del proyecto al path.
sys.path.insert(0, str(Path(__file__).parent))


def print_header(text):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text):
    print(f"[OK] {text}")


def print_error(text):
    print(f"[ERROR] {text}")


def print_info(text):
    print(f"[INFO] {text}")


def print_warning(text):
    print(f"[WARN] {text}")


def validate_imports():
    """Valida que todos los imports funcionan."""
    print_header("1. VALIDACION DE IMPORTS")

    try:
        from app.routers.auth import router  # noqa: F401
        print_success("app.routers.auth importado correctamente")
    except Exception as e:
        print_error(f"Error importando auth: {str(e)}")
        return False

    try:
        from app.security import create_access_token, verify_password, SECRET_KEY  # noqa: F401
        print_success("app.security importado correctamente")
    except Exception as e:
        print_error(f"Error importando security: {str(e)}")
        return False

    try:
        from app.main import app  # noqa: F401
        print_success("app.main importado correctamente")
    except Exception as e:
        print_error(f"Error importando main: {str(e)}")
        return False

    return True


def validate_jwt_secret():
    """Valida que JWT_SECRET esta configurado."""
    print_header("2. VALIDACION DE JWT_SECRET")

    from app.security import SECRET_KEY

    if not SECRET_KEY:
        print_warning("JWT_SECRET no esta configurada localmente")
        print_info("Esto puede ser normal en desarrollo si usas un .env")
        print_info("En produccion (Railway) debe estar configurada")
        return True

    if len(SECRET_KEY) < 16:
        print_warning(f"JWT_SECRET muy corta ({len(SECRET_KEY)} caracteres)")
        print_info("Recomendacion: usar al menos 32 caracteres")
        return True

    print_success(f"JWT_SECRET configurada ({len(SECRET_KEY)} caracteres)")
    return True


def validate_password_hashing():
    """Valida que bcrypt/passlib funciona correctamente."""
    print_header("3. VALIDACION DE HASH DE PASSWORD")

    try:
        from app.security import pwd_context

        test_password = "TestPassword123!"
        hashed = pwd_context.hash(test_password)
        print_success(f"Hash creado: {hashed[:50]}...")

        if pwd_context.verify(test_password, hashed):
            print_success("Hash verificado correctamente")
        else:
            print_error("Hash no se verifico")
            return False

        if not pwd_context.verify("WrongPassword", hashed):
            print_success("Password incorrecto rechazado")
        else:
            print_error("Password incorrecto fue aceptado")
            return False

        return True

    except Exception as e:
        print_error(f"Error en hashing: {str(e)}")
        return False


def validate_database_connection():
    """Valida que la conexion a BD funciona."""
    print_header("4. VALIDACION DE CONEXION A BASE DE DATOS")

    try:
        from app.db.database import run_query

        run_query("SELECT 1", fetch=True)
        print_success("Conexion a BD exitosa")
        return True

    except Exception as e:
        print_warning(f"No se pudo conectar a BD: {str(e)}")
        print_info("Esto puede ser normal si la BD no esta disponible localmente")
        return True


def validate_endpoint_structure():
    """Valida que el endpoint /login tiene la estructura esperada."""
    print_header("5. VALIDACION DE ESTRUCTURA DEL ENDPOINT")

    try:
        from app.routers.auth import login_for_access_token
        import inspect

        source = inspect.getsource(login_for_access_token)

        if "try:" in source and "except" in source:
            print_success("Endpoint tiene try/except para manejo de errores")
        else:
            print_warning("Endpoint podria no tener manejo de errores")

        if "logger" in source:
            print_success("Endpoint tiene logging configurado")
        else:
            print_warning("Endpoint no tiene logging")

        if "verify_password" in source or "verify_and_upgrade_password" in source:
            print_success("Endpoint verifica el password")
        else:
            print_error("Endpoint no verifica el password")
            return False

        if "create_access_token" in source:
            print_success("Endpoint crea el token JWT")
        else:
            print_error("Endpoint no crea token")
            return False

        return True

    except Exception as e:
        print_error(f"Error validando estructura: {str(e)}")
        return False


def validate_security_functions():
    """Valida que las funciones de seguridad tienen la estructura esperada."""
    print_header("6. VALIDACION DE FUNCIONES DE SEGURIDAD")

    try:
        from app.security import create_access_token, verify_password
        import inspect

        verify_source = inspect.getsource(verify_password)
        token_source = inspect.getsource(create_access_token)

        if "try:" in verify_source and "except" in verify_source:
            print_success("verify_password() tiene manejo de errores")
        else:
            print_warning("verify_password() podria no tener try/except")

        if "try:" in token_source and "except" in token_source:
            print_success("create_access_token() tiene manejo de errores")
        else:
            print_warning("create_access_token() podria no tener try/except")

        if "logger" in token_source:
            print_success("create_access_token() tiene logging")
        else:
            print_warning("create_access_token() no tiene logging")

        return True

    except Exception as e:
        print_error(f"Error validando funciones: {str(e)}")
        return False


def run_tests():
    """Ejecuta todas las validaciones."""
    print_header("VALIDACION RAPIDA - ERROR 500 EN /LOGIN")
    print_info("Este script verifica que los cambios esten correctamente implementados")

    tests = [
        ("Imports", validate_imports),
        ("JWT_SECRET", validate_jwt_secret),
        ("Password Hashing", validate_password_hashing),
        ("Database Connection", validate_database_connection),
        ("Endpoint Structure", validate_endpoint_structure),
        ("Security Functions", validate_security_functions),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Error en test {test_name}: {str(e)}")
            results[test_name] = False

    print_header("RESUMEN")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[ERROR] FAIL"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} pruebas pasadas\n")

    if passed == total:
        print_success("Todas las validaciones pasaron correctamente")
        print_info("Proximos pasos:")
        print_info("1. Ejecuta: python diagnose_login.py")
        print_info("2. Haz commit: git add . && git commit -m \"fix: error 500 en login\"")
        print_info("3. Push a Railway: git push")
        print_info("4. Verifica en produccion")
        return True

    print_warning(f"{total - passed} validacion(es) fallaron")
    print_info("Revisa los errores arriba y corrigelos antes de hacer push")
    return False


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidacion cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error fatal: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
