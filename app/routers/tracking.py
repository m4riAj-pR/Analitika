"""
app/routers/tracking.py

Endpoints públicos de tracking (sin autenticación JWT):
  - GET /c/{id_link}  → landing page + registro de clic
  - POST /conversion/public → registro de conversión con token firmado

Controles de integridad implementados:
  1. Rate limiting por IP (slowapi): 10/min en clics, 3/min en conversiones
  2. Detección básica de bots por User-Agent (sin denunciarlo: sirve la página sin registrar clic)
  3. Deduplicación de clics: mismo ip_hash + id_link en ventana de 30 segundos
  4. Token HMAC firmado: generado al registrar el clic, validado al registrar la conversión
  5. Ventana de validez de conversión: 48 horas desde el clic
  6. Unicidad de conversión por clic: un token/clic solo genera una conversión

Endpoints autenticados de analytics también en este router (requieren JWT).
"""
import hashlib
import logging
import json
import urllib.request
from datetime import datetime

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from app.db.database import run_query
from app.main import limiter
from app.security import get_current_user, filter_financial_kpis
from app.services.a_service import ensure_campaign_access
from app.services.tracking_integrity import (
    generate_click_token,
    validate_click_token,
    is_duplicate_click,
    is_conversion_already_registered,
    is_click_valid,
    is_bot_user_agent,
)

logger = logging.getLogger(__name__)

router = APIRouter()
env = Environment(loader=FileSystemLoader("app/templates"))


def get_country_from_ip(ip: str, id_click: int):
    try:
        if ip in ["127.0.0.1", "localhost", "::1"]:
            run_query("UPDATE clicks SET country = %s WHERE id_click = %s", ("Colombia", id_click))
            return

        is_private = False
        if ip.startswith("192.168.") or ip.startswith("10."):
            is_private = True
        elif ip.startswith("172."):
            try:
                second_octet = int(ip.split(".")[1])
                if 16 <= second_octet <= 31:
                    is_private = True
            except Exception:
                pass

        if is_private:
            run_query("UPDATE clicks SET country = %s WHERE id_click = %s", ("Colombia", id_click))
            return

        with urllib.request.urlopen(
            f"http://ip-api.com/json/{ip}?fields=status,country", timeout=3
        ) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "success":
                run_query(
                    "UPDATE clicks SET country = %s WHERE id_click = %s",
                    (data.get("country"), id_click),
                )
            else:
                run_query("UPDATE clicks SET country = %s WHERE id_click = %s", ("Colombia", id_click))
    except Exception as e:
        try:
            run_query("UPDATE clicks SET country = %s WHERE id_click = %s", ("Colombia", id_click))
        except Exception:
            pass
        logger.warning("Error en geolocalización: %s", e)


# ---------------------------------------------------------------------------
# GET /c/{id_link} — Landing page pública con registro de clic
# Rate limit: 10 peticiones por IP por minuto
# ---------------------------------------------------------------------------

@router.get("/c/{id_link}")
@limiter.limit("10/minute")
def landing_campana(id_link: int, request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint público. Registra el clic y renderiza la landing page.
    Incluye el token firmado en el HTML para que la conversión pueda validarse.
    """
    # 1. Verificar que el link existe
    resultado = run_query(
        """
        SELECT c.name, c.description
        FROM tracking_links tl
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE tl.id_link = %s
        """,
        (id_link,),
        fetch=True,
    )
    if not resultado:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Link de seguimiento no encontrado")

    campana = resultado[0]

    # 2. Extraer IP (Railway usa X-Forwarded-For)
    forwarded = request.headers.get("x-forwarded-for")
    ip_address = (
        forwarded.split(",")[0].strip() if forwarded else (request.client.host or "127.0.0.1")
    )
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
    user_agent = request.headers.get("user-agent", "")

    # 3. Detección de bots por User-Agent
    # Estrategia: servir la página sin registrar el clic (bot no sabe que fue detectado)
    if is_bot_user_agent(user_agent):
        template = env.get_template("campana.html")
        html = template.render(
            nombre=campana["name"],
            descripcion=campana["description"],
            click_token="",  # Token vacío — no habrá conversión válida
        )
        return HTMLResponse(content=html)

    # 4. Deduplicación: misma IP + link en ventana de 30s → no insertar
    if is_duplicate_click(ip_hash, id_link):
        # Servir la página pero sin registrar un nuevo clic
        # Recuperar el id_click existente para que el botón de conversión funcione
        existing = run_query(
            """
            SELECT id_click FROM clicks
            WHERE ip_address_hash = %s AND id_link = %s
            ORDER BY clicked_at DESC LIMIT 1
            """,
            (ip_hash, id_link),
            fetch=True,
        )
        existing_id = existing[0]["id_click"] if existing else None
        click_token = generate_click_token(existing_id) if existing_id else ""
        template = env.get_template("campana.html")
        html = template.render(
            nombre=campana["name"],
            descripcion=campana["description"],
            click_token=click_token,
        )
        return HTMLResponse(content=html)

    # 5. Capturar UTMs
    utm_source = request.query_params.get("utm_source")
    utm_medium = request.query_params.get("utm_medium")
    utm_campaign = request.query_params.get("utm_campaign")
    utm_term = request.query_params.get("utm_term")
    utm_content = request.query_params.get("utm_content")

    # 6. Registrar clic
    id_click = run_query(
        """
        INSERT INTO clicks (
            id_link, ip_address_hash, user_agent, referrer, clicked_at,
            utm_source, utm_medium, utm_campaign, utm_term, utm_content
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            id_link,
            ip_hash,
            user_agent,
            request.headers.get("referer"),
            datetime.utcnow(),
            utm_source,
            utm_medium,
            utm_campaign,
            utm_term,
            utm_content,
        ),
        fetch=False,
        return_lastrowid=True,
    )

    # 7. Geolocalización en background
    if id_click and ip_address != "127.0.0.1":
        background_tasks.add_task(get_country_from_ip, ip_address, id_click)

    # 8. Generar token firmado para vincular este clic con la futura conversión
    click_token = generate_click_token(id_click) if id_click else ""

    # 9. Renderizar HTML con el token (no el id_click en texto plano)
    template = env.get_template("campana.html")
    html = template.render(
        nombre=campana["name"],
        descripcion=campana["description"],
        click_token=click_token,
    )
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# POST /conversion/public — Registro de conversión con token firmado
# Rate limit: 3 peticiones por IP por minuto
# ---------------------------------------------------------------------------

@router.post("/conversion/public")
@limiter.limit("3/minute")
async def register_public_conversion(request: Request):
    """
    Endpoint público. Registra una conversión validando el token firmado generado
    durante el clic. Rechaza: tokens inválidos, expirados o ya usados.
    """
    try:
        data = await request.json()
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Solicitud inválida")

    click_token = data.get("click_token", "")
    revenue = float(data.get("revenue", 0.0))
    type_conv = data.get("type", "lead")
    notes = data.get("notes", "")

    # 1. Validar token: firma + expiración
    is_valid, id_click, reason = validate_click_token(click_token)
    if not is_valid:
        logger.warning(
            "Conversión rechazada — razón=%s ip=%s",
            reason,
            request.client.host if request.client else "desconocida",
        )
        # Respuesta genérica: no revelar detalles internos al posible atacante
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar tu solicitud. Por favor, visita el enlace nuevamente.",
        )

    # 2. Verificar que el clic existe en BD (defensa en profundidad)
    if not is_click_valid(id_click):
        logger.warning("Conversión con id_click inexistente — id_click=%s", id_click)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar tu solicitud. Por favor, visita el enlace nuevamente.",
        )

    # 3. Verificar unicidad: un clic solo puede generar una conversión
    if is_conversion_already_registered(id_click):
        logger.info("Intento de conversión duplicada — id_click=%s", id_click)
        # Respuesta amigable al usuario real que hace doble clic
        return {"ok": True, "message": "Tu solicitud ya fue registrada anteriormente."}

    # 4. Registrar la conversión
    run_query(
        "INSERT INTO conversions (id_click, revenue, type, notes) VALUES (%s, %s, %s, %s)",
        (id_click, revenue, type_conv, notes),
    )

    logger.info("Conversión registrada — id_click=%s type=%s", id_click, type_conv)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Endpoints autenticados de analytics (requieren JWT)
# ---------------------------------------------------------------------------

@router.get("/stats/{id_campaign}")
def get_metricas(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))

    clics = run_query(
        """
        SELECT COUNT(c.id_click) as total
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        """,
        (id_campaign,),
        fetch=True,
    )

    conversiones = run_query(
        """
        SELECT COUNT(cv.id_conversion) as total,
               COALESCE(SUM(cv.revenue), 0) as ingresos
        FROM conversions cv
        JOIN clicks c ON cv.id_click = c.id_click
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        """,
        (id_campaign,),
        fetch=True,
    )

    campana = run_query(
        "SELECT spent FROM campaigns WHERE id_campaign = %s",
        (id_campaign,),
        fetch=True,
    )

    total_clics = clics[0]["total"] or 0
    total_conversiones = conversiones[0]["total"] or 0
    ingresos = float(conversiones[0]["ingresos"] or 0)
    spent = float(campana[0]["spent"] or 0) if campana else 0.0

    cpc = round(spent / total_clics, 2) if total_clics > 0 else 0
    cpa = round(spent / total_conversiones, 2) if total_conversiones > 0 else 0
    roi = round(((ingresos - spent) / spent) * 100, 2) if spent > 0 else 0
    roas = round(ingresos / spent, 2) if spent > 0 else 0
    conversion_rate = round((total_conversiones / total_clics) * 100, 2) if total_clics > 0 else 0
    aov = round(ingresos / total_conversiones, 2) if total_conversiones > 0 else 0

    metricas = {
        "clics": total_clics,
        "conversiones": total_conversiones,
        "ingresos": ingresos,
        "spent": spent,
        "cpc": cpc,
        "cpa": cpa,
        "roi": roi,
        "roas": roas,
        "conversion_rate": conversion_rate,
        "aov": aov,
    }

    return filter_financial_kpis(metricas, current_user)


@router.get("/stats/{id_campaign}/clics-por-dia")
def get_clics_por_dia(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))
    resultado = run_query(
        """
        SELECT DATE(c.clicked_at) as fecha, COUNT(c.id_click) as clics
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        GROUP BY DATE(c.clicked_at)
        ORDER BY fecha ASC
        """,
        (id_campaign,),
        fetch=True,
    )
    return {"data": [{"fecha": str(r["fecha"]), "clics": r["clics"]} for r in resultado]}


@router.get("/stats/{id_campaign}/tabla-clics")
def get_tabla_clics(id_campaign: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id_campaign, current_user.get("id_role"))
    resultado = run_query(
        """
        SELECT
            c.clicked_at,
            COALESCE(c.country, 'Desconocido') as pais,
            c.ip_address_hash as ip,
            c.user_agent,
            c.utm_source,
            c.utm_medium,
            c.utm_campaign,
            c.utm_term,
            c.utm_content
        FROM clicks c
        JOIN tracking_links tl ON c.id_link = tl.id_link
        WHERE tl.id_campaign = %s
        ORDER BY c.clicked_at DESC
        LIMIT 50
        """,
        (id_campaign,),
        fetch=True,
    )
    return {
        "data": [
            {
                "created_at": r["clicked_at"].isoformat() + "Z" if r["clicked_at"] else None,
                "fecha": r["clicked_at"].strftime("%Y-%m-%d") if r["clicked_at"] else "N/A",
                "hora": r["clicked_at"].strftime("%H:%M:%S") if r["clicked_at"] else "N/A",
                "pais": r["pais"],
                "ip": r["ip"][:8] if r["ip"] else "N/A",
                "user_agent": r["user_agent"] or "N/A",
                "utm_source": r["utm_source"] or "N/A",
                "utm_medium": r["utm_medium"] or "N/A",
                "utm_campaign": r["utm_campaign"] or "N/A",
                "utm_term": r["utm_term"] or "N/A",
                "utm_content": r["utm_content"] or "N/A",
            }
            for r in resultado
        ]
    }
