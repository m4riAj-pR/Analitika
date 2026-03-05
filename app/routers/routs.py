from fastapi import APIRouter, HTTPException
from app.schemas.dispositivos import Dispositivo
from app.schemas.sensor import Sensor
from app.schemas.lectura import Lectura
from app.services.a_service import (
    insert_dispositivo,
    insert_sensor,
    insert_lectura,
    read_table
)

router = APIRouter(prefix="/analitika", tags=["Analitika"])

VALID_TABLES = {"dispositivo", "sensor", "lectura"}


@router.get("/")
def root():
    return {"message": "API conectada a analitika_db"}


@router.post("/dispositivo")
def create_dispositivo(data: Dispositivo):
    insert_dispositivo(data)
    return {"ok": True}


@router.post("/sensor")
def create_sensor(data: Sensor):
    insert_sensor(data)
    return {"ok": True}


@router.post("/lectura")
def create_lectura(data: Lectura):
    insert_lectura(data)
    return {"ok": True}


@router.get("/select/{table}")
def get_table(table: str):
    if table not in VALID_TABLES:
        raise HTTPException(400, "tabla inválida")

    return read_table(table)