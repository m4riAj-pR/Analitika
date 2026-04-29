#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en el endpoint /login
Valida:
1. Configuración de JWT_SECRET en el entorno
2. Formato de hashes de contraseña en la base de datos
3. Funcionalidad de verify_password
"""

import os
import sys
from pathlib import Path

# Agrega el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import run_query
from app.security import pwd_context, SECRET_KEY
from passlib.exc import InvalidHashError

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_secret_key():
    """Verifica si JWT_SECRET está configurado"""
    print_section("1. VERIFICACIÓN DE JWT_SECRET")
    
    if SECRET_KEY:
        print(f"✓ JWT_SECRET está configurado")
        print(f"  Longitud: {len(SECRET_KEY)} caracteres")
        # Muestra solo los primeros y últimos caracteres por seguridad
        masked = SECRET_KEY[:5] + "*" * (len(SECRET_KEY)-10) + SECRET_KEY[-5:]
        print(f"  Valor (enmascarado): {masked}")
    else:
        print("✗ CRÍTICO: JWT_SECRET NO ESTÁ CONFIGURADO")
        print("  Esto causará error 500 al intentar crear tokens")
        print("  Acción: Define JWT_SECRET en Railway variables")
    
    return bool(SECRET_KEY)

def check_password_hashes():
    """Inspecciona los hashes de contraseña en la base de datos"""
    print_section("2. INSPECCIÓN DE HASHES DE CONTRASEÑA EN BD")
    
    try:
        result = run_query(
            """
            SELECT u.id_user, p.email, u.password_hash
            FROM users u
            JOIN persons p ON u.id_person = p.id_person
            LIMIT 5
            """,
            fetch=True
        )
        
        if not result:
            print("✗ No hay usuarios en la base de datos")
            return False
        
        print(f"Encontrados {len(result)} usuarios (primeros 5):\n")
        
        has_valid_hashes = True
        for user in result:
            email = user["email"]
            hash_value = user["password_hash"]
            
            print(f"Usuario: {email}")
            print(f"  Hash: {hash_value[:50]}..." if len(hash_value) > 50 else f"  Hash: {hash_value}")
            
            # Verifica formato de bcrypt
            if hash_value.startswith("$2"):
                print("  ✓ Formato bcrypt correcto ($2a$, $2b$, $2y$)")
            else:
                print("  ✗ ADVERTENCIA: Hash no parece ser bcrypt válido")
                has_valid_hashes = False
                
                if hash_value.startswith("$md5$") or len(hash_value) == 32:
                    print("     Parece ser MD5 - necesita re-hashing")
                elif len(hash_value) < 20:
                    print("     Hash muy corto - posiblemente texto plano")
            print()
        
        return has_valid_hashes
    
    except Exception as e:
        print(f"✗ Error al conectar a la base de datos: {str(e)}")
        return False

def test_password_verification(email: str, password: str):
    """Prueba la verificación de contraseña con un usuario específico"""
    print_section("3. PRUEBA DE VERIFICACIÓN DE CONTRASEÑA")
    print(f"Probando con usuario: {email}\n")
    
    try:
        result = run_query(
            """
            SELECT u.password_hash FROM users u
            JOIN persons p ON u.id_person = p.id_person
            WHERE LOWER(p.email) = LOWER(%s)
            """,
            (email,),
            fetch=True
        )
        
        if not result:
            print(f"✗ Usuario {email} no encontrado")
            return False
        
        hash_value = result[0]["password_hash"]
        print(f"Hash en BD: {hash_value[:50]}...")
        
        try:
            is_valid = pwd_context.verify(password, hash_value)
            if is_valid:
                print(f"✓ Contraseña CORRECTA para {email}")
            else:
                print(f"✗ Contraseña INCORRECTA para {email}")
            return is_valid
        
        except InvalidHashError as e:
            print(f"✗ ERROR: Hash de formato inválido")
            print(f"  Detalles: {str(e)}")
            print(f"  El hash no es un hash bcrypt válido")
            return False
        except Exception as e:
            print(f"✗ ERROR inesperado al verificar: {str(e)}")
            return False
    
    except Exception as e:
        print(f"✗ Error al acceder a la base de datos: {str(e)}")
        return False

def test_hash_creation():
    """Prueba la creación y verificación de un hash"""
    print_section("4. PRUEBA DE CREACIÓN DE HASH")
    
    test_password = "TestPassword123!"
    print(f"Contraseña de prueba: {test_password}\n")
    
    try:
        # Crea un hash
        hashed = pwd_context.hash(test_password)
        print(f"Hash generado: {hashed}")
        print(f"Longitud: {len(hashed)} caracteres\n")
        
        # Verifica que funcione
        is_valid = pwd_context.verify(test_password, hashed)
        if is_valid:
            print("✓ Hash verificado correctamente")
        else:
            print("✗ Hash no se verificó")
        
        # Intenta con contraseña incorrecta
        is_valid_wrong = pwd_context.verify("WrongPassword", hashed)
        if not is_valid_wrong:
            print("✓ Contraseña incorrecta rechazada correctamente")
        else:
            print("✗ Error: contraseña incorrecta fue aceptada")
        
        return True
    
    except Exception as e:
        print(f"✗ Error en creación de hash: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("    DIAGNÓSTICO DE ENDPOINT /LOGIN")
    print("="*60)
    
    checks = {
        "JWT_SECRET": check_secret_key(),
        "Password Hashes": check_password_hashes(),
        "Hash Creation": test_hash_creation(),
    }
    
    # Test de verificación de contraseña interactivo
    print_section("PRUEBA INTERACTIVA (opcional)")
    try:
        email = input("Ingresa email de usuario para probar (Enter para saltar): ").strip()
        if email:
            password = input("Ingresa contraseña: ").strip()
            checks["Password Verification"] = test_password_verification(email, password)
    except KeyboardInterrupt:
        print("\n(Prueba interactiva cancelada)")
    
    # Resumen
    print_section("RESUMEN DE DIAGNÓSTICO")
    all_pass = all(checks.values())
    
    for check_name, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check_name}: {status}")
    
    print()
    if all_pass:
        print("✓ Todas las verificaciones pasaron.")
        print("  Si aún tienes error 500, revisa los logs del servidor.")
    else:
        print("✗ Se encontraron problemas. Revisa los detalles arriba.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
