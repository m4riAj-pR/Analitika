# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse

def get_connection():
    # Priorizar DATABASE_URL de las variables de entorno
    db_url = os.getenv("DATABASE_URL")
    
    # Fallback solo para desarrollo local si no hay env var
    if not db_url:
        db_url = "mysql+pymysql://root:KALtosOfuJlKoDdiUpveLhvfvjcOBPKd@metro.proxy.rlwy.net:10028/railway"

    url = urlparse(db_url)

    try:
        conn = pymysql.connect(
            host=url.hostname,
            port=url.port or 3306,
            user=url.username or "root",
            password=url.password or "KALtosOfuJlKoDdiUpveLhvfvjcOBPKd",
            database=url.path.lstrip('/'),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        # En producción no imprimimos el error crudo para no filtrar credenciales
        raise RuntimeError(f"Error de conexión a la base de datos")

def run_query(sql, params=None, fetch=False, return_lastrowid=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)

            result = None
            lastrowid = None

            if fetch:
                result = cur.fetchall()

            if return_lastrowid:
                lastrowid = cur.lastrowid

        conn.commit()

        if return_lastrowid:
            return lastrowid

        if fetch:
            return result

        return None

    except Exception as e:
        if conn:
            conn.rollback()
        raise e

    finally:
        if conn:
            conn.close()