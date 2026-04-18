from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from app.db.database import run_query

router = APIRouter()
env = Environment(loader=FileSystemLoader("app/templates"))

@router.get("/c/{id_link}")
def landing_campana(id_link: int, request: Request):
    # 1. Busca el link y la campaña
    resultado = run_query("""
        SELECT c.name, c.description
        FROM tracking_links tl
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE tl.id_link = %s
    """, (id_link,), fetch=True)

    campana = resultado[0] if resultado else {"name": "Campaña no encontrada", "description": ""}

    # 2. Registra el clic
    run_query("""
        INSERT INTO clicks (id_link, ip_address, user_agent, referrer, clicked_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        id_link,
        request.client.host,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
        datetime.utcnow()
    ))

    # 3. Renderiza el HTML
    template = env.get_template("campana.html")
    html = template.render(nombre=campana["name"], descripcion=campana["description"])
    return HTMLResponse(content=html)