from app.db.database import run_query
from fastapi import HTTPException,status
import pymysql

from app.schemas.usuarios import Usuario
from app.schemas.campanas import Campana
from app.schemas.canales import Canal
from app.schemas.campanas_canales import CampanaCanal
from app.schemas.clics import Clic
from app.schemas.conversiones import Conversion
#--------
def insert_usuario(data: Usuario):
    try:
        run_query(
            "INSERT INTO usuarios (email, nombres, apellidos, rol, password_hash) VALUES (%s, %s, %s, %s, %s)",
            (data.email, data.nombres, data.apellidos, data.rol, data.password_hash)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar usuario: {e}")

def update_usuario_service(id_usuario: int, data: Usuario):
    try:
        run_query(
            "UPDATE usuarios SET email=%s, nombres=%s, apellidos=%s, rol=%s, password_hash=%s WHERE id_usuario=%s",
            (data.email, data.nombres, data.apellidos, data.rol, data.password_hash, id_usuario)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar usuario: {e}")

def delete_usuario_service(id_usuario: int):
    result = run_query("SELECT COUNT(*) AS total FROM campanas WHERE usuario_id=%s", (id_usuario,), fetch=True)
    if result[0]['total'] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el usuario: tiene campañas asociadas."
        )
    run_query("DELETE FROM usuarios WHERE id_usuario=%s", (id_usuario,))


# --------------------
def insert_campana(data: Campana):
    try:
        run_query(
            "INSERT INTO campanas (usuario_id, nombre, presupuesto, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s)",
            (data.usuario_id, data.nombre, float(data.presupuesto), data.fecha_inicio, data.fecha_fin)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar campaña: {e}")

def update_campana_service(id_campana: int, data: Campana):
    try:
        run_query(
            "UPDATE campanas SET usuario_id=%s, nombre=%s, presupuesto=%s, fecha_inicio=%s, fecha_fin=%s WHERE id_campana=%s",
            (data.usuario_id, data.nombre, float(data.presupuesto), data.fecha_inicio, data.fecha_fin, id_campana)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar campaña: {e}")

def delete_campana_service(id_campana: int):

    result_rel = run_query(
        "SELECT COUNT(*) AS total FROM campanas_canales WHERE campana_id=%s",
        (id_campana,), fetch=True
    )

    result_clics = run_query(
        "SELECT COUNT(*) AS total FROM clics WHERE campana_id=%s",
        (id_campana,), fetch=True
    )
 
    result_conversiones = run_query(
        "SELECT COUNT(*) AS total FROM conversiones WHERE campana_id=%s",
        (id_campana,), fetch=True
    )

    if result_rel[0]['total'] > 0 or result_clics[0]['total'] > 0 or result_conversiones[0]['total'] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la campaña: existen registros asociados (canales, clics o conversiones)."
        )

    run_query("DELETE FROM campanas WHERE id_campana=%s", (id_campana,))


# --------------------

def insert_canal(data: Canal):
    try:
        run_query("INSERT INTO canales (nombre) VALUES (%s)", (data.nombre,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar canal: {e}")

def update_canal_service(id_canal: int, data: Canal):
    try:
        run_query("UPDATE canales SET nombre=%s WHERE id_canal=%s", (data.nombre, id_canal))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar canal: {e}")

def delete_canal_service(id_canal: int):
    result = run_query("SELECT COUNT(*) AS total FROM campanas_canales WHERE canal_id=%s", (id_canal,), fetch=True)
    if result[0]['total'] > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: existen campañas asociadas.")
    try:
        run_query("DELETE FROM canales WHERE id_canal=%s", (id_canal,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar canal: {e}")


# --------------------

def insert_campana_canal(data: CampanaCanal):
    try:
        run_query("INSERT INTO campanas_canales (campana_id, canal_id) VALUES (%s, %s)", (data.campana_id, data.canal_id))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar campaña-canal: {e}")

def update_campana_canal_service(old_campana_id: int, old_canal_id: int, data: CampanaCanal):
    try:
        run_query(
            "UPDATE campanas_canales SET campana_id=%s, canal_id=%s WHERE campana_id=%s AND canal_id=%s",
            (data.campana_id, data.canal_id, old_campana_id, old_canal_id)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar campaña-canal: {e}")

def delete_campana_service(id_campana: int):
    result1 = run_query("SELECT COUNT(*) AS total FROM campanas_canales WHERE campana_id=%s", (id_campana,), fetch=True)
    result2 = run_query("SELECT COUNT(*) AS total FROM clics WHERE campana_id=%s", (id_campana,), fetch=True)
    result3 = run_query("SELECT COUNT(*) AS total FROM conversiones WHERE campana_id=%s", (id_campana,), fetch=True)

    if result1[0]['total'] > 0 or result2[0]['total'] > 0 or result3[0]['total'] > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: existen registros asociados a esta campaña.")

    run_query("DELETE FROM campanas WHERE id_campana=%s", (id_campana,))


# --------------------

def insert_clic(data: Clic):
    try:
        run_query(
            "INSERT INTO clics (campana_id, fecha_hora, dispositivo, canal_id) VALUES (%s, %s, %s, %s)",
            (data.campana_id, data.fecha_hora, data.dispositivo, data.canal_id)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar clic: {e}")

def update_clic_service(id_clics: int, data: Clic):
    try:
        run_query(
            "UPDATE clics SET campana_id=%s, fecha_hora=%s, dispositivo=%s, canal_id=%s WHERE id_clics=%s",
            (data.campana_id, data.fecha_hora, data.dispositivo, data.canal_id, id_clics)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar clic: {e}")

def delete_clic_service(id_clics: int):
    try:
        run_query("DELETE FROM clics WHERE id_clics=%s", (id_clics,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar clic: {e}")


# --------------------

def insert_conversion(data: Conversion):
    try:
        run_query(
            "INSERT INTO conversiones (campana_id, ingreso, fecha_hora, canal_id, origen) VALUES (%s, %s, %s, %s, %s)",
            (data.campana_id, float(data.ingreso), data.fecha_hora, data.canal_id, data.origen)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar conversión: {e}")

def update_conversion_service(id_conversion: int, data: Conversion):
    try:
        run_query(
            "UPDATE conversiones SET campana_id=%s, ingreso=%s, fecha_hora=%s, canal_id=%s, origen=%s WHERE id_conversion=%s",
            (data.campana_id, float(data.ingreso), data.fecha_hora, data.canal_id, data.origen, id_conversion)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar conversión: {e}")

def delete_conversion_service(id_conversion: int):
    try:
        run_query("DELETE FROM conversiones WHERE id_conversion=%s", (id_conversion,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar conversión: {e}")


# --------------------

def read_table(table: str):
    allowed_tables = {
        "usuarios", "campanas", "canales", "campanas_canales", "clics", "conversiones"
    }
    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Tabla '{table}' no permitida")

    id_column_map = {
        "usuarios": "id_usuario",
        "campanas": "id_campana",
        "canales": "id_canal",
        "campanas_canales": "campana_id",
        "clics": "id_clics",
        "conversiones": "id_conversion"
    }
    id_col = id_column_map[table]

    return run_query(f"SELECT * FROM {table} ORDER BY {id_col}", fetch=True)