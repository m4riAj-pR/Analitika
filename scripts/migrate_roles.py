import os
import sys
import logging

# Añadir la raíz del proyecto al sys.path para poder importar el módulo 'app'
# Se asume que este archivo está en 'scripts/'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.config import load_env_file
from app.db.database import get_connection

# Cargar variables de entorno desde el .env en la raíz
load_env_file()

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def migrate_roles() -> None:
    """
    Standardizes the roles in the database by resetting the roles table 
    and inserting the predefined roles with fixed IDs (1: Super_Admin, 2: Owner, 3: Manager).
    
    This operation disables foreign key checks temporarily to allow the reset.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            logger.info("Starting role migration...")
            
            # Desactivar cheques de llaves foráneas en esta sesión
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            # Limpiar roles anteriores
            cur.execute("DELETE FROM roles;")
            logger.info("Previous roles cleared.")
            
            # Insertar roles con IDs específicos
            roles = [
                (1, 'Super_Admin'),
                (2, 'Owner'),
                (3, 'Manager')
            ]
            
            query = "INSERT INTO roles (id_role, name) VALUES (%s, %s)"
            cur.executemany(query, roles)
            
            # Reactivar cheques
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            
            conn.commit()
            logger.info("Roles migrated successfully with IDs 1, 2, and 3.")
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration failed: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_roles()

