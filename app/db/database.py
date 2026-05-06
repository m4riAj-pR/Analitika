# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse


def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL no configurada. Verifica tu archivo .env.")

    url = urlparse(db_url)
    database = url.path.lstrip("/")
    if not url.hostname or not url.username or not database:
        raise RuntimeError("DATABASE_URL invalida. Usa mysql+pymysql://usuario:password@host:puerto/base")

    try:
        conn = pymysql.connect(
            host=url.hostname,
            port=url.port or 3306,
            user=url.username,
            password=url.password or "",
            database=database,
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