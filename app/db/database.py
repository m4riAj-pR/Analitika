import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

pool = SimpleConnectionPool(
    1, 10,
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "analitika_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", 5432)
)


def run_query(sql: str, params=None, fetch: bool = False):
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)

        if fetch:
            return cur.fetchall()

        conn.commit()
    finally:
        pool.putconn(conn)