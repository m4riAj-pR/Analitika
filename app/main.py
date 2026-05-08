import os
from app.config import load_env_file

# Cargar variables de entorno antes de importar cualquier otro módulo de la aplicación
load_env_file()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, routs, tracking, notifications, admin


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


app = FastAPI(
    title="Analitika API",
    description="API para gestionar campanas digitales",
    version="1.0.0"
)


@app.on_event("startup")
def validate_environment():
    """Valida que todas las variables de entorno críticas estén configuradas."""
    required_vars = {
        "JWT_SECRET": "Autenticación JWT",
        "DATABASE_URL": "Conexión a Base de Datos"
    }

    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"  - {var_name} ({description})")

    if missing_vars:
        error_msg = "ERROR CRÍTICO: Variables de entorno no configuradas:\n" + "\n".join(missing_vars)
        error_msg += "\n\nVerifica tu archivo .env o las variables en Railway/Render."
        raise RuntimeError(error_msg)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(routs.router)
app.include_router(tracking.router)
app.include_router(auth.router)
app.include_router(notifications.router, prefix="/analitika/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/analitika/admin", tags=["admin"])


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API principal"}
