import os
import pymysql
from pymysql.cursors import DictCursor

connection = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "analitika_db"),
    port=int(os.getenv("DB_PORT", 3306)),
    cursorclass=DictCursor
)


def run_query(sql: str, params=None, fetch: bool = False):
    with connection.cursor() as cur:
        cur.execute(sql, params)

        if fetch:
            return cur.fetchall()

        connection.commit()