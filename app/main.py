from fastapi import FastAPI
from app.routers import routs  # importa el archivo de rutas que creaste

# Crear la aplicación principal
app = FastAPI(
    title="Analitika API",
    description="API para gestionar usuarios, campañas, canales, clics y conversiones",
    version="1.0.0"
)

# Incluir el router de analitika
app.include_router(routs.router)

# Ruta raíz opcional para la aplicación principal
@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API principal"}
