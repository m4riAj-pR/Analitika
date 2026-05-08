from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import json
import urllib.request
from app.db.database import run_query
from app.security import get_current_user
from app.services.a_service import ensure_campaign_access

router = APIRouter()
env = Environment(loader=FileSystemLoader("app/templates"))

def get_country_from_ip(ip: str, id_click: int):
    try:
        # No usamos ip-api con localhost
        if ip in ["127.0.0.1", "localhost", "::1"]:
            return
        
        with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=status,country", timeout=3) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "success":
                run_query("UPDATE clicks SET country = %s WHERE id_click = %s", (data.get("country"), id_click))
    except Exception as e:
        print(f"Error en geolocalización: {e}")

@router.get("/c/{id_link}")
def landing_campana(id_link: int, request: Request, background_tasks: BackgroundTasks):
    # 1. Busca el link y la campaña
    resultado = run_query("""
        SELECT c.name, c.description
        FROM tracking_links tl
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE tl.id_link = %s
    """, (id_link,), fetch=True)

    if not resultado:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Link de seguimiento no encontrado")

    campana = resultado[0]

    import hashlib
    # Si estamos detrás de un proxy (Railway, etc), usamos X-Forwarded-For
    forwarded = request.headers.get("x-forwarded-for")
    ip_address = forwarded.split(",")[0] if forwarded else (request.client.host or "127.0.0.1")
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

    # 2. Registra el clic inicial
    id_click = run_query("""
        INSERT INTO clicks (id_link, ip_address_hash, user_agent, referrer, clicked_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        id_link,
        ip_hash,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
        datetime.utcnow()
    ), fetch=False, return_lastrowid=True) # Necesitamos que run_query devuelva el ID

    # 3. Lanzar geolocalización en segundo plano
    if id_click and ip_address != "127.0.0.1":
        background_tasks.add_task(get_country_from_ip, ip_address, id_click)

    # 4. Renderiza el HTML
    template = env.get_template("campana.html")
    html = template.render(nombre=campana["name"], descripcion=campana["description"])
    return HTMLResponse(content=html)
@router.get("/stats/{id_campaign}")
def get_metricas(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign)
    # Clics totales
    clics = run_query("""
        SELECT COUNT(c.id_click) as total
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
    """, (id_campaign,), fetch=True)

    # Conversiones e ingresos
    conversiones = run_query("""
        SELECT COUNT(cv.id_conversion) as total, 
               COALESCE(SUM(cv.revenue), 0) as ingresos
        FROM conversions cv
        JOIN clicks c ON cv.id_click = c.id_click
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
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
    roi = round(((ingresos - spent) / spent) * 100, 2) if spent > 0 else 0

    roas = round(ingresos / spent, 2) if spent > 0 else 0
    conversion_rate = round((total_conversiones / total_clics) * 100, 2) if total_clics > 0 else 0
    aov = round(ingresos / total_conversiones, 2) if total_conversiones > 0 else 0

    return {
        "clics": total_clics,
        "conversiones": total_conversiones,
        "ingresos": ingresos,
        "spent": spent,
        "cpc": cpc,
        "cpa": cpa,
        "roi": roi,
        "roas": roas,
        "conversion_rate": conversion_rate,
        "aov": aov
    }
@router.get("/stats/{id_campaign}/clics-por-dia")
def get_clics_por_dia(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign)
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
def get_tabla_clics(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign)
    resultado = run_query("""
        SELECT 
            c.clicked_at,
            COALESCE(c.country, 'Desconocido') as pais,
            c.ip_address_hash as ip,
            c.user_agent
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        ORDER BY c.clicked_at DESC
        LIMIT 50
    """, (id_campaign,), fetch=True)

    return {"data": [
        {
            "created_at": r["clicked_at"].isoformat() + "Z" if r["clicked_at"] else None,
            "fecha": r["clicked_at"].strftime("%Y-%m-%d") if r["clicked_at"] else "N/A",
            "hora": r["clicked_at"].strftime("%H:%M:%S") if r["clicked_at"] else "N/A",
            "pais": r["pais"],
            "ip": r["ip"][:8] if r["ip"] else "N/A",
            "user_agent": r["user_agent"] or "N/A"
        }
        for r in resultado
    ]} 
    
