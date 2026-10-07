import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import run_query
from app.services.meta_ads_service import sync_connection_metrics

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def sync_all_active_connections():
    """
    Tarea programada para sincronizar métricas de todas las conexiones activas.
    Recorre cada conexión de forma aislada para garantizar que un fallo o rate limit
    en una cuenta no interrumpa la sincronización de las demás.
    """
    logger.info("Iniciando sincronización programada de cuentas publicitarias...")
    try:
        active_connections = run_query("""
            SELECT id_connection, id_company, provider, external_account_id
            FROM ad_account_connections
            WHERE status = 'active'
        """, fetch=True)
    except Exception as e:
        logger.error(f"Error consultando conexiones activas para el job de sincronización: {e}")
        return

    if not active_connections:
        logger.info("No hay conexiones activas pendientes de sincronización.")
        return

    for conn in active_connections:
        id_conn = conn["id_connection"]
        provider = conn["provider"]
        ext_acc = conn["external_account_id"]
        logger.info(f"Sincronizando conexión {id_conn} (Proveedor: {provider}, Cuenta: {ext_acc})...")

        try:
            if provider == "meta":
                res = sync_connection_metrics(id_conn)
                logger.info(f"Resultado sincronización conexión {id_conn}: {res}")
            else:
                logger.info(f"Proveedor '{provider}' configurado pero sin sincronizador activo en esta fase.")
        except Exception as e:
            # Aislamiento de fallos: registrar y continuar con la siguiente conexión
            logger.error(f"Excepción aislada sincronizando conexión {id_conn}: {e}", exc_info=True)

    logger.info("Sincronización programada finalizada.")


def start_scheduler():
    """Inicializa y arranca el planificador en segundo plano."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return

    # Intervalo de sincronización en horas (por defecto 6 horas)
    try:
        hours = int(os.getenv("META_SYNC_INTERVAL_HOURS", "6"))
    except ValueError:
        hours = 6

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        sync_all_active_connections,
        trigger=IntervalTrigger(hours=hours),
        id="sync_ad_accounts_job",
        name="Sincronización periódica de métricas de cuentas publicitarias",
        replace_existing=True
    )
    _scheduler.start()
    logger.info(f"Scheduler de sincronización de publicidad iniciado (Intervalo: cada {hours}h).")


def stop_scheduler():
    """Detiene el planificador de manera segura al apagar la aplicación."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler de sincronización detenido.")
        _scheduler = None
