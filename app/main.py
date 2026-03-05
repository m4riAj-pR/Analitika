from fastapi import FastAPI
from routers import routs as route

app = FastAPI(title="Analitika API")

app.include_router(route)