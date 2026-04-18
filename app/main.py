from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import routs, tracking

app = FastAPI(
    title="Analitika API",
    description="API para gestionar campañas digitales",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(routs.router)
app.include_router(tracking.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API principal"}