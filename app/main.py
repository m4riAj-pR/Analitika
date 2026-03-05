from fastapi import FastAPI
from app.routers.routs import router

app = FastAPI(title="Analitika API")

app.include_router(router)