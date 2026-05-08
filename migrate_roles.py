from app.db.database import get_connection

def migrate_roles():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Desactivar cheques de llaves foráneas en esta sesión
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            # Limpiar roles anteriores (esto es seguro por el SET anterior)
            cur.execute("DELETE FROM roles;")
            
            # Insertar roles con IDs específicos
            roles = [
                (1, 'Super_Admin'),
                (2, 'Owner'),
                (3, 'Manager')
            ]
            cur.executemany("INSERT INTO roles (id_role, name) VALUES (%s, %s)", roles)
            
            # Reactivar cheques
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            
            conn.commit()
            print("Roles migrados exitosamente con IDs 1, 2 y 3.")
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_roles()
