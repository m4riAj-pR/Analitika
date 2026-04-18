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
@router.get("/stats/{id_campaign}")
def get_metricas(id_campaign: int):
    # Clics totales
    clics = run_query("""
        SELECT COUNT(c.id_click) as total
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
    """, (id_campaign,), fetch=True)

    # Conversiones e ingresos
    conversiones = run_query("""
        SELECT COUNT(id_conversion) as total, 
               COALESCE(SUM(revenue), 0) as ingresos
        FROM conversions
        WHERE id_campaign = %s
    """, (id_campaign,), fetch=True)

    # Presupuesto invertido
    campana = run_query("""
        SELECT spent FROM campaigns WHERE id_campaign = %s
    """, (id_campaign,), fetch=True)

    total_clics = clics[0]["total"] or 0
    total_conversiones = conversiones[0]["total"] or 0
    ingresos = float(conversiones[0]["ingresos"] or 0)
    spent = float(campana[0]["spent"] or 0)

    cpc = round(spent / total_clics, 2) if total_clics > 0 else 0
    cpa = round(spent / total_conversiones, 2) if total_conversiones > 0 else 0
    roi = round((ingresos - spent) / spent * 100, 2) if spent > 0 else 0

    return {
        "clics": total_clics,
        "conversiones": total_conversiones,
        "ingresos": ingresos,
        "spent": spent,
        "cpc": cpc,
        "cpa": cpa,
        "roi": roi
    }
@router.get("/stats/{id_campaign}/clics-por-dia")
def get_clics_por_dia(id_campaign: int):
    resultado = run_query("""
        SELECT DATE(c.clicked_at) as fecha, COUNT(c.id_click) as clics
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        GROUP BY DATE(c.clicked_at)
        ORDER BY fecha ASC
    """, (id_campaign,), fetch=True)

    return {"data": [
        {"fecha": str(r["fecha"]), "clics": r["clics"]}
        for r in resultado
    ]}
@router.get("/stats/{id_campaign}/tabla-clics")
def get_tabla_clics(id_campaign: int):
    resultado = run_query("""
        SELECT 
            DATE(c.clicked_at) as fecha,
            TIME(c.clicked_at) as hora,
            COALESCE(c.country, 'Desconocido') as pais
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        ORDER BY c.clicked_at DESC
    """, (id_campaign,), fetch=True)

    return {"data": [
        {
            "fecha": str(r["fecha"]),
            "hora": str(r["hora"]),
            "pais": r["pais"]
        }
        for r in resultado
    ]} 
    
