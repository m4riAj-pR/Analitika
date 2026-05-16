import logging
from app.db.database import run_query

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Ejecuta migraciones automáticas para asegurar que el esquema de la base de datos
    esté siempre actualizado con las últimas características.
    """
    logger.info("Iniciando verificación de esquema de base de datos...")
    
    try:
        # 1. Migración para soporte UTM en la tabla 'clicks'
        utm_columns = [
            ("utm_source", "VARCHAR(100)"),
            ("utm_medium", "VARCHAR(100)"),
            ("utm_campaign", "VARCHAR(100)"),
            ("utm_term", "VARCHAR(100)"),
            ("utm_content", "VARCHAR(100)")
        ]
        
        for col_name, col_type in utm_columns:
            # Verificar si la columna ya existe
            check = run_query(f"SHOW COLUMNS FROM clicks LIKE %s", (col_name,), fetch=True)
            if not check:
                logger.info(f"Migración: Agregando columna {col_name} a la tabla clicks...")
                run_query(f"ALTER TABLE clicks ADD COLUMN {col_name} {col_type} DEFAULT NULL")
        
        # 3. Migración para columna 'budget' en la tabla 'campaigns'
        check_budget = run_query("SHOW COLUMNS FROM campaigns LIKE 'budget'", fetch=True)
        if not check_budget:
            logger.info("Migración: Agregando columna budget a la tabla campaigns...")
            run_query("ALTER TABLE campaigns ADD COLUMN budget DECIMAL(10, 2) NOT NULL DEFAULT '0.00' AFTER spent")

        logger.info("Verificación de esquema completada exitosamente.")
        
    except Exception as e:
        logger.error(f"Error crítico durante las migraciones: {e}")
        # No relanzamos la excepción para no bloquear el inicio de la app, 
        # a menos que sea algo que realmente impida el funcionamiento básico.
