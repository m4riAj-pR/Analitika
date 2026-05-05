# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "ERROR CRÍTICO: DATABASE_URL no está configurada en las variables de entorno. "
            "Verifica tu archivo .env o las variables en Railway."
        )

    if not database_url.startswith(("mysql://", "mysql+pymysql://")):
        raise RuntimeError(
            "ERROR CRÍTICO: DATABASE_URL debe ser una URL MySQL válida. "
            "Formato esperado: mysql+pymysql://user:password@host:port/database"
        )

    # Parsear la URL de Railway
    url = urlparse(database_url)

    return pymysql.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:],  # quita el "/"
        cursorclass=DictCursor
    )

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
        conn.rollback()
        raise e

    finally:
        conn.close()