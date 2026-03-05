from fastapi import FastAPI
from app.routers import routs  

app = FastAPI(
    title="Analitika API",
    description="API para gestionar usuarios, campañas, canales, clics y conversiones",
    version="1.0.0"
)

app.include_router(routs.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API principal"}
