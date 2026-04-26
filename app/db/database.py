# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse

def get_connection():
    database_url = os.getenv("DATABASE_URL")

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

def run_query(sql, params=None, fetch=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
        conn.commit()
    finally:
        conn.close()