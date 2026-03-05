from app.db.database import run_query


def insert_dispositivo(data):
    run_query(
        "INSERT INTO dispositivo (id, w, n) VALUES (%s, %s, %s)",
        (data.id, data.w, data.n)
    )


def insert_sensor(data):
    run_query(
        "INSERT INTO sensor (id, referencia, descripcion, dispositivo_id) VALUES (%s, %s, %s, %s)",
        (data.id, data.referencia, data.descripcion, data.dispositivo_id)
    )


def insert_lectura(data):
    run_query(
        "INSERT INTO lectura (id, fechahora, valor, sensor_id) VALUES (%s, %s, %s, %s)",
        (data.id, data.fechahora, data.valor, data.sensor_id)
    )


def read_table(table: str):
    return run_query(
        f"SELECT * FROM {table} ORDER BY id",
        fetch=True
    )