from app.db.database import run_query

# -------------------------
# SERVICIOS USUARIOS
# -------------------------
def insert_usuario(data):
    run_query(
        "INSERT INTO usuarios (email, nombres, apellidos, rol, password_hash) VALUES (%s, %s, %s, %s, %s)",
        (data.email, data.nombres, data.apellidos, data.rol, data.password_hash)
    )

def update_usuario_service(id_usuario, data):
    run_query(
        "UPDATE usuarios SET email=%s, nombres=%s, apellidos=%s, rol=%s, password_hash=%s WHERE id_usuario=%s",
        (data.email, data.nombres, data.apellidos, data.rol, data.password_hash, id_usuario)
    )

def delete_usuario_service(id_usuario):
    run_query("DELETE FROM usuarios WHERE id_usuario=%s", (id_usuario,))


# -------------------------
# SERVICIOS CAMPANAS
# -------------------------
def insert_campana(data):
    run_query(
        "INSERT INTO campanas (usuario_id, nombre, presupuesto, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s)",
        (data.usuario_id, data.nombre, data.presupuesto, data.fecha_inicio, data.fecha_fin)
    )

def update_campana_service(id_campana, data):
    run_query(
        "UPDATE campanas SET usuario_id=%s, nombre=%s, presupuesto=%s, fecha_inicio=%s, fecha_fin=%s WHERE id_campana=%s",
        (data.usuario_id, data.nombre, data.presupuesto, data.fecha_inicio, data.fecha_fin, id_campana)
    )

def delete_campana_service(id_campana):
    run_query("DELETE FROM campanas WHERE id_campana=%s", (id_campana,))


# -------------------------
# SERVICIOS CANALES
# -------------------------
def insert_canal(data):
    run_query(
        "INSERT INTO canales (nombre) VALUES (%s)",
        (data.nombre,)
    )

def update_canal_service(id_canal, data):
    run_query(
        "UPDATE canales SET nombre=%s WHERE id_canal=%s",
        (data.nombre, id_canal)
    )

def delete_canal_service(id_canal):
    run_query("DELETE FROM canales WHERE id_canal=%s", (id_canal,))


# -------------------------
# SERVICIOS CAMPANAS_CANALES
# -------------------------
def insert_campana_canal(data):
    run_query(
        "INSERT INTO campanas_canales (campana_id, canal_id) VALUES (%s, %s)",
        (data.campana_id, data.canal_id)
    )

def update_campana_canal_service(old_campana_id, old_canal_id, data):
    # Para actualizar la PK compuesta necesitamos identificar ambos campos
    run_query(
        "UPDATE campanas_canales SET campana_id=%s, canal_id=%s WHERE campana_id=%s AND canal_id=%s",
        (data.campana_id, data.canal_id, old_campana_id, old_canal_id)
    )

def delete_campana_canal_service(campana_id, canal_id):
    run_query(
        "DELETE FROM campanas_canales WHERE campana_id=%s AND canal_id=%s",
        (campana_id, canal_id)
    )


# -------------------------
# SERVICIOS CLICS
# -------------------------
def insert_clic(data):
    run_query(
        "INSERT INTO clics (campana_id, fecha_hora, dispositivo, canal_id) VALUES (%s, %s, %s, %s)",
        (data.campana_id, data.fecha_hora, data.dispositivo, data.canal_id)
    )

def update_clic_service(id_clics, data):
    run_query(
        "UPDATE clics SET campana_id=%s, fecha_hora=%s, dispositivo=%s, canal_id=%s WHERE id_clics=%s",
        (data.campana_id, data.fecha_hora, data.dispositivo, data.canal_id, id_clics)
    )

def delete_clic_service(id_clics):
    run_query("DELETE FROM clics WHERE id_clics=%s", (id_clics,))


# -------------------------
# SERVICIOS CONVERSIONES
# -------------------------
def insert_conversion(data):
    run_query(
        "INSERT INTO conversiones (campana_id, ingreso, fecha_hora, canal_id, origen) VALUES (%s, %s, %s, %s, %s)",
        (data.campana_id, data.ingreso, data.fecha_hora, data.canal_id, data.origen)
    )

def update_conversion_service(id_conversion, data):
    run_query(
        "UPDATE conversiones SET campana_id=%s, ingreso=%s, fecha_hora=%s, canal_id=%s, origen=%s WHERE id_conversion=%s",
        (data.campana_id, data.ingreso, data.fecha_hora, data.canal_id, data.origen, id_conversion)
    )

def delete_conversion_service(id_conversion):
    run_query("DELETE FROM conversiones WHERE id_conversion=%s", (id_conversion,))


# -------------------------
# SERVICIO GENERICO PARA LEER TABLAS
# -------------------------
def read_table(table: str):
    allowed_tables = {
        "usuarios", "campanas", "canales", "campanas_canales", "clics", "conversiones"
    }
    if table not in allowed_tables:
        raise ValueError(f"Tabla '{table}' no permitida")
    
    # Se usa 'id' correcto según tabla para ordenar
    id_column_map = {
        "usuarios": "id_usuario",
        "campanas": "id_campana",
        "canales": "id_canal",
        "campanas_canales": "campana_id",  # PK compuesta, ordenamos por campana_id primero
        "clics": "id_clics",
        "conversiones": "id_conversion"
    }
    id_col = id_column_map[table]
    
    return run_query(
        f"SELECT * FROM {table} ORDER BY {id_col}",
        fetch=True
    )