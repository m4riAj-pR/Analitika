# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse

def get_connection():
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DATABASE_URL no está definida")

    url = urlparse(db_url)

    print("DB CONNECT →", {
        "host": url.hostname,
        "port": url.port,
        "user": url.username,
        "db": url.path
    })

    try:
        print("Username: ", url.username)
        print("Password: ", url.password)
        print("Database: ", url.path.lstrip('/'))
        print("Host: ", url.hostname)
        print("Port: ", url.port)

        conn = pymysql.connect(
            host=url.hostname,
            port=url.port or 3306,
            user="root",
            password= "KALtosOfuJlKoDdiUpveLhvfvjcOBPKd",
            database=url.path.lstrip('/'),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print("DB CONNECTION ERROR:", str(e))
        raise RuntimeError("No se pudo conectar a la base de datos")

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