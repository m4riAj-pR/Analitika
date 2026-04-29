#!/usr/bin/env python3
"""
Script para re-hashear contraseñas si están en un formato incorrecto.

ADVERTENCIA: Este script asume que:
1. Las contraseñas están en texto plano en la BD
2. O están en un formato que se puede convertir a bcrypt

Si las contraseñas están en un formato hash irreversible (como MD5 sin salt),
este script NO funcionará. Los usuarios tendrán que usar "Forgot Password".
"""

import os
import sys
from pathlib import Path
from getpass import getpass
import hashlib
import re

# Agrega el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import run_query
from app.security import pwd_context

def is_bcrypt_hash(password_hash: str) -> bool:
    """Verifica si un hash es bcrypt válido"""
    return bool(password_hash.startswith(("$2a$", "$2b$", "$2y$")))

def is_md5(password_hash: str) -> bool:
    """Verifica si parece ser MD5"""
    return bool(re.match(r"^[a-f0-9]{32}$", password_hash.lower()))

def get_all_users():
    """Obtiene todos los usuarios con sus contraseñas hash"""
    try:
        result = run_query(
            """
            SELECT u.id_user, p.email, u.password_hash
            FROM users u
            JOIN persons p ON u.id_person = p.id_person
            """,
            fetch=True
        )
        return result
    except Exception as e:
        print(f"Error al conectar a BD: {str(e)}")
        return None

def main():
    print("\n" + "="*70)
    print("  RE-HASHEADOR DE CONTRASEÑAS - CONVERTIR A BCRYPT")
    print("="*70)
    
    print("\n⚠️  ADVERTENCIAS IMPORTANTES:")
    print("  1. Este script modifica la BD. HAGA BACKUP PRIMERO.")
    print("  2. Solo funciona si las contraseñas están en TEXTO PLANO.")
    print("  3. Si son hashes MD5/SHA1 sin las contraseñas originales,")
    print("     los usuarios deberán usar 'Forgot Password'.")
    print("\n")
    
    # Confirmación
    confirmation = input("¿Deseas continuar? (escribe 'SI' para confirmar): ").strip().upper()
    if confirmation != "SI":
        print("Operación cancelada.")
        return
    
    users = get_all_users()
    if not users:
        print("No se pudieron obtener usuarios de la BD.")
        return
    
    print(f"\nEncontrados {len(users)} usuarios.\n")
    
    # Análisis de hashes
    bcrypt_count = 0
    plaintext_count = 0
    md5_count = 0
    unknown_count = 0
    
    hash_samples = {}
    
    for user in users:
        hash_val = user["password_hash"]
        
        if is_bcrypt_hash(hash_val):
            bcrypt_count += 1
        elif is_md5(hash_val):
            md5_count += 1
            if "md5" not in hash_samples:
                hash_samples["md5"] = (user["email"], hash_val[:50])
        elif len(hash_val) < 50 and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:',.<>?/" for c in hash_val):
            plaintext_count += 1
            if "plaintext" not in hash_samples:
                hash_samples["plaintext"] = (user["email"], hash_val[:50])
        else:
            unknown_count += 1
            if "unknown" not in hash_samples:
                hash_samples["unknown"] = (user["email"], hash_val[:50])
    
    print("ANÁLISIS DE HASHES ACTUALES:")
    print(f"  • Bcrypt válidos: {bcrypt_count}")
    print(f"  • MD5: {md5_count}")
    print(f"  • Texto plano: {plaintext_count}")
    print(f"  • Desconocido: {unknown_count}\n")
    
    if hash_samples:
        print("EJEMPLOS:")
        for fmt, (email, sample) in hash_samples.items():
            print(f"  • {fmt.upper()}: {email}")
            print(f"    Hash: {sample}...\n")
    
    if bcrypt_count == len(users):
        print("✓ Todas las contraseñas ya son bcrypt válidas.")
        print("  No es necesario ejecutar este script.")
        return
    
    if plaintext_count > 0:
        print("✓ Se encontraron contraseñas en texto plano.")
        print("  Estas pueden ser convertidas a bcrypt.\n")
    
    if md5_count > 0:
        print("✗ Se encontraron hashes MD5.")
        print("  Estos NO pueden ser convertidos (son irreversibles).")
        print("  Opciones:")
        print("    1. Usar 'Forgot Password' para que usuarios reestablezcan")
        print("    2. Convertir manualmente si tienes acceso a contraseñas originales\n")
    
    if unknown_count > 0:
        print("⚠️  Se encontraron hashes de formato desconocido.")
        print("    Revisa manualmente qué tipo son.\n")
    
    # Preguntar qué hacer
    if plaintext_count == 0:
        print("No hay contraseñas en texto plano para convertir.")
        print("Operación finalizada.")
        return
    
    print("\n" + "-"*70)
    option = input("\n¿Convertir contraseñas en texto plano a bcrypt? (si/no): ").strip().lower()
    
    if option not in ["si", "yes", "s", "y"]:
        print("Operación cancelada.")
        return
    
    # Conversión
    print("\n🔄 Iniciando conversión de contraseñas...\n")
    
    converted = 0
    errors = 0
    
    for user in users:
        id_user = user["id_user"]
        email = user["email"]
        password_hash = user["password_hash"]
        
        # Solo convierte si no es bcrypt válido
        if is_bcrypt_hash(password_hash):
            continue
        
        if plaintext_count > 0 and len(password_hash) < 100:
            # Asume que es texto plano
            try:
                new_hash = pwd_context.hash(password_hash)
                
                # Actualiza en BD
                run_query(
                    "UPDATE users SET password_hash = %s WHERE id_user = %s",
                    (new_hash, id_user)
                )
                
                converted += 1
                print(f"✓ {email}: convertido a bcrypt")
            
            except Exception as e:
                errors += 1
                print(f"✗ {email}: ERROR - {str(e)}")
    
    print(f"\n" + "="*70)
    print(f"RESUMEN:")
    print(f"  • Contraseñas convertidas: {converted}")
    print(f"  • Errores: {errors}")
    print(f"  • Sin cambios: {len(users) - converted - errors}")
    print("="*70)
    
    if converted > 0:
        print(f"\n✓ {converted} contraseña(s) fueron convertida(s) exitosamente.")
        print("  Recarga la BD en Railway para que tomen efecto los cambios.")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
