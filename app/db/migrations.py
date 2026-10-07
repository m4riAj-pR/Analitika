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

        # 4. Migración para asegurar eliminación de columna 'lastname' en 'persons'
        check_lastname = run_query("SHOW COLUMNS FROM persons LIKE 'lastname'", fetch=True)
        if check_lastname:
            logger.info("Migración: Eliminando columna obsoleta 'lastname' de la tabla persons...")
            run_query("ALTER TABLE persons DROP COLUMN lastname")

        # 5. Migración: Crear tablas para conexiones de cuentas publicitarias y métricas externas
        run_query("""
            CREATE TABLE IF NOT EXISTS `ad_account_connections` (
              `id_connection` INT NOT NULL AUTO_INCREMENT,
              `id_company` INT NOT NULL,
              `provider` ENUM('meta', 'google', 'tiktok') NOT NULL,
              `external_account_id` VARCHAR(100) NOT NULL,
              `account_name` VARCHAR(150) DEFAULT NULL,
              `access_token` VARCHAR(2048) NOT NULL,
              `refresh_token` VARCHAR(2048) DEFAULT NULL,
              `token_expires_at` DATETIME DEFAULT NULL,
              `status` ENUM('active', 'expired', 'revoked', 'error') NOT NULL DEFAULT 'active',
              `status_message` VARCHAR(255) DEFAULT NULL,
              `connected_by` INT NOT NULL,
              `connected_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
              `last_sync_at` DATETIME DEFAULT NULL,
              `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_connection`),
              UNIQUE KEY `uq_company_provider_account` (`id_company`, `provider`, `external_account_id`),
              CONSTRAINT `fk_ad_conn_company` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE ON UPDATE CASCADE,
              CONSTRAINT `fk_ad_conn_user` FOREIGN KEY (`connected_by`) REFERENCES `users` (`id_user`) ON DELETE RESTRICT ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        run_query("""
            CREATE TABLE IF NOT EXISTS `campaign_external_mapping` (
              `id_mapping` INT NOT NULL AUTO_INCREMENT,
              `id_campaign` INT NOT NULL,
              `id_connection` INT NOT NULL,
              `external_campaign_id` VARCHAR(100) NOT NULL,
              `external_campaign_name` VARCHAR(150) DEFAULT NULL,
              `sync_enabled` TINYINT(1) NOT NULL DEFAULT '1',
              `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
              `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_mapping`),
              UNIQUE KEY `uq_campaign_connection` (`id_campaign`, `id_connection`),
              UNIQUE KEY `uq_conn_ext_campaign` (`id_connection`, `external_campaign_id`),
              CONSTRAINT `fk_mapping_campaign` FOREIGN KEY (`id_campaign`) REFERENCES `campaigns` (`id_campaign`) ON DELETE CASCADE ON UPDATE CASCADE,
              CONSTRAINT `fk_mapping_connection` FOREIGN KEY (`id_connection`) REFERENCES `ad_account_connections` (`id_connection`) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        run_query("""
            CREATE TABLE IF NOT EXISTS `campaign_external_metrics` (
              `id_metric` INT NOT NULL AUTO_INCREMENT,
              `id_mapping` INT NOT NULL,
              `metric_date` DATE NOT NULL,
              `impressions` INT NOT NULL DEFAULT '0',
              `spend` DECIMAL(10, 2) NOT NULL DEFAULT '0.00',
              `external_clicks` INT NOT NULL DEFAULT '0',
              `reach` INT NOT NULL DEFAULT '0',
              `fetched_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
              `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id_metric`),
              KEY `idx_mapping_date` (`id_mapping`, `metric_date`),
              CONSTRAINT `fk_metrics_mapping` FOREIGN KEY (`id_mapping`) REFERENCES `campaign_external_mapping` (`id_mapping`) ON DELETE CASCADE ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        logger.info("Verificación de esquema completada exitosamente.")
        
    except Exception as e:
        logger.error(f"Error crítico durante las migraciones: {e}")
        # No relanzamos la excepción para no bloquear el inicio de la app, 
        # a menos que sea algo que realmente impida el funcionamiento básico.
