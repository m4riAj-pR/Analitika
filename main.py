import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# =========================
# CONEXIÓN A analitika_db
# =========================
pool = SimpleConnectionPool(
    1, 10,
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "analitika_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", 5432)
)

# =========================
# MODELOS
# =========================
class Dispositivo(BaseModel):
    id: int
    w: str
    n: str

class Sensor(BaseModel):
    id: int
    referencia: str
    descripcion: str
    dispositivo_id: int

class Lectura(BaseModel):
    id: int
    fechahora: str
    valor: float
    sensor_id: int


# =========================
# HELPERS
# =========================
def run_query(sql, params=None, fetch=False):
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
    finally:
        pool.putconn(conn)


# =========================
# RUTAS
# =========================

@app.get("/")
async def root():
    return {"message": "API conectada a analitika_db"}


@app.post("/dispositivo")
async def insert_dispositivo(data: Dispositivo):
    run_query(
        "INSERT INTO dispositivo (id, w, n) VALUES (%s, %s, %s)",
        (data.id, data.w, data.n)
    )
    return {"ok": True}


@app.post("/sensor")
async def insert_sensor(data: Sensor):
    run_query(
        "INSERT INTO sensor (id, referencia, descripcion, dispositivo_id) VALUES (%s, %s, %s, %s)",
        (data.id, data.referencia, data.descripcion, data.dispositivo_id)
    )
    return {"ok": True}


@app.post("/lectura")
async def insert_lectura(data: Lectura):
    run_query(
        "INSERT INTO lectura (id, fechahora, valor, sensor_id) VALUES (%s, %s, %s, %s)",
        (data.id, data.fechahora, data.valor, data.sensor_id)
    )
    return {"ok": True}


VALID_TABLES = {"dispositivo", "sensor", "lectura"}

@app.get("/select/{table}")
async def read_table(table: str):
    if table not in VALID_TABLES:
        raise HTTPException(400, "tabla inválida")

    rows = run_query(
        f"SELECT * FROM {table} ORDER BY id",
        fetch=True
    )
    return rows
