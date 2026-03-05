from fastapi import APIRouter
from app.schemas.usuarios import Usuario
from app.schemas.campanas import Campana
from app.schemas.canales import Canal
from app.schemas.campanas_canales import CampanaCanal
from app.schemas.clics import Clic
from app.schemas.conversiones import Conversion

from app.services.a_service import *

router = APIRouter(prefix="/analitika", tags=["Analitika"])

VALID_TABLES = {
    "usuarios",
    "campanas",
    "canales",
    "campanas_canales",
    "clics",
    "conversiones"
}

@router.get("/")
def root():
    return {"message": "API conectada a analitika_db"}

# ---------------- RUTAS USUARIOS ----------------

@router.post("/usuarios")
def create_usuario(data: Usuario):
    insert_usuario(data)
    return {"ok": True}

@router.get("/usuarios")
def get_usuarios():
    return read_table("usuarios")

@router.put("/usuarios/{id}")
def update_usuario(id: int, data: Usuario):
    update_usuario_service(id, data)
    return {"ok": True}

@router.delete("/usuarios/{id}")
def delete_usuario(id: int):
    delete_usuario_service(id)
    return {"ok": True}

# ---------------- RUTAS CAMPANAS ----------------

@router.post("/campanas")
def create_campana(data: Campana):
    insert_campana(data)
    return {"ok": True}

@router.get("/campanas")
def get_campanas():
    return read_table("campanas")

@router.put("/campanas/{id}")
def update_campana(id: int, data: Campana):
    update_campana_service(id, data)
    return {"ok": True}

@router.delete("/campanas/{id}")
def delete_campana(id: int):
    delete_campana_service(id)
    return {"ok": True}

# ---------------- RUTAS CANALES ----------------

@router.post("/canales")
def create_canal(data: Canal):
    insert_canal(data)
    return {"ok": True}

@router.get("/canales")
def get_canales():
    return read_table("canales")

@router.put("/canales/{id}")
def update_canal(id: int, data: Canal):
    update_canal_service(id, data)
    return {"ok": True}

@router.delete("/canales/{id}")
def delete_canal(id: int):
    delete_canal_service(id)
    return {"ok": True}

# ---------------- RUTAS CAMPANAS_CANALES ----------------

@router.post("/campanas_canales")
def create_campana_canal(data: CampanaCanal):
    insert_campana_canal(data)
    return {"ok": True}

@router.get("/campanas_canales")
def get_campanas_canales():
    return read_table("campanas_canales")

@router.put("/campanas_canales/{id}")
def update_campana_canal(id: int, data: CampanaCanal):
    update_campana_canal_service(id, data)
    return {"ok": True}

@router.delete("/campanas_canales/{id}")
def delete_campana_canal(id: int):
    delete_campana_canal_service(id)
    return {"ok": True}

# ---------------- RUTAS CLICS ----------------

@router.post("/clics")
def create_clic(data: Clic):
    insert_clic(data)
    return {"ok": True}

@router.get("/clics")
def get_clics():
    return read_table("clics")

@router.put("/clics/{id}")
def update_clic(id: int, data: Clic):
    update_clic_service(id, data)
    return {"ok": True}

@router.delete("/clics/{id}")
def delete_clic(id: int):
    delete_clic_service(id)
    return {"ok": True}

# ---------------- RUTAS CONVERSIONES ----------------

@router.post("/conversiones")
def create_conversion(data: Conversion):
    insert_conversion(data)
    return {"ok": True}

@router.get("/conversiones")
def get_conversiones():
    return read_table("conversiones")

@router.put("/conversiones/{id}")
def update_conversion(id: int, data: Conversion):
    update_conversion_service(id, data)
    return {"ok": True}

@router.delete("/conversiones/{id}")
def delete_conversion(id: int):
    delete_conversion_service(id)
    return {"ok": True}
