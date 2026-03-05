# app/db/database.py
import os
import pymysql
from pymysql.cursors import DictCursor

# Conexión global a la base de datos
connection = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "analitika_db"),
    port=int(os.getenv("DB_PORT", 3306)),
    cursorclass=DictCursor
)

# Función genérica para ejecutar queries
def run_query(sql: str, params=None, fetch: bool = False):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        connection.commit()