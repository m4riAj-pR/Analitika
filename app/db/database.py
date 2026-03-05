# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "analitika_db"),
        port=int(os.getenv("DB_PORT", 3306)),
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