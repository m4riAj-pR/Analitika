from app.db.database import run_query
from fastapi import HTTPException, status
import pymysql

from app.schemas.persons import Person
from app.schemas.role import Role
from app.schemas.permissions import Permission
from app.schemas.role_has_permissions import RoleHasPermission
from app.schemas.companies import Company
from app.schemas.users import User
from app.schemas.user_company import UserCompany
from app.schemas.campaigns import Campaign
from app.schemas.channels import Channel
from app.schemas.tracking_links import TrackingLink
from app.schemas.clicks import Click
from app.schemas.conversions import Conversion
from app.security import hash_password, is_bcrypt_hash

# NOTIFICATIONS & ANALYSIS logic is at the end of the file


def generate_auto_recommendations(id_user: int):
    """
    Motor de análisis de campañas de marketing digital siguiendo reglas de umbrales.
    """
    company_ids = get_user_company_ids(id_user)
    if not company_ids: return
    
    in_clause, params = build_in_clause(company_ids)
    
    campañas = run_query(f"""
        SELECT c.id_campaign, c.name, c.spent, c.id_company
        FROM campaigns c
        WHERE c.id_company IN {in_clause} AND c.status = 'active'
    """, params, fetch=True)
    
    for camp in campañas:
        cid = camp['id_campaign']
        stats = run_query("""
            SELECT 
                COUNT(ck.id_click) as clics,
                COALESCE(SUM(cv.revenue), 0) as ingresos,
                COUNT(cv.id_conversion) as conversiones
            FROM tracking_links tl
            LEFT JOIN clicks ck ON tl.id_link = ck.id_link AND ck.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            LEFT JOIN conversions cv ON ck.id_click = cv.id_click
            WHERE tl.id_campaign = %s
        """, (cid,), fetch=True)[0]
        
        clics = stats['clics'] or 0
        ingresos = float(stats['ingresos'] or 0)
        conversiones = stats['conversiones'] or 0
        spent = float(camp['spent'] or 0)
        
        clics_prev = run_query("""
            SELECT COUNT(ck.id_click) as clics
            FROM tracking_links tl
            JOIN clicks ck ON tl.id_link = ck.id_link
            WHERE tl.id_campaign = %s 
              AND ck.created_at BETWEEN DATE_SUB(NOW(), INTERVAL 14 DAY) AND DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (cid,), fetch=True)[0]['clics'] or 0

        cpc = (spent / clics) if clics > 0 else 0
        cr = (conversiones / clics * 100) if clics > 0 else 0
        roi_pesos = ingresos - spent
        growth = ((clics - clics_prev) / clics_prev * 100) if clics_prev > 0 else (0 if clics == 0 else 100)

        alertas = []
        analisis = []

        if roi_pesos < 0:
            nivel_roi = "CRÍTICO"
            alertas.append(f"ROI CRÍTICO en '{camp['name']}': Pérdida de ${abs(round(roi_pesos))}.")
            msg_roi = "Pausa anuncios de alto CPC, revisa landing y audita público."
        elif roi_pesos <= 50000:
            nivel_roi = "BAJO"
            msg_roi = "Inversión recuperada, margen mínimo. Optimiza palabras clave y A/B testing."
        elif roi_pesos <= 200000:
            nivel_roi = "ACEPTABLE"
            msg_roi = "Hay ganancia, espacio de mejora. Escala mejores anuncios y haz remarketing."
        elif roi_pesos <= 500000:
            nivel_roi = "BUENO"
            msg_roi = "Campaña rentable. Escala presupuesto 20-30% semanal."
        else:
            nivel_roi = "EXCELENTE"
            msg_roi = "Alto rendimiento. Escala agresivamente y automatiza pujas."
        analisis.append(f"ROI: {nivel_roi} (${round(roi_pesos)}). {msg_roi}")

        if cpc > 3000:
            nivel_cpc = "CRÍTICO"
            alertas.append(f"CPC CRÍTICO: ${round(cpc)} por clic.")
            msg_cpc = "Pausa campaña, audita segmentación o cambia de canal."
        elif cpc > 1500:
            nivel_cpc = "ALTO"
            msg_cpc = "Refina segmentación y agrega palabras clave negativas."
        elif cpc >= 500:
            nivel_cpc = "ACEPTABLE"
            msg_cpc = "Mejora Quality Score y prueba otros horarios."
        else:
            nivel_cpc = "EFICIENTE"
            msg_cpc = "Mantén segmentación y escala volumen."
        analisis.append(f"CPC: {nivel_cpc} (${round(cpc)}). {msg_cpc}")

        if cr < 1:
            nivel_cr = "CRÍTICO"
            alertas.append(f"TASA CONV. CRÍTICA: {round(cr, 2)}%.")
            msg_cr = "Audita landing page, instala mapas de calor y simplifica compra."
        elif cr < 3:
            nivel_cr = "BAJO"
            msg_cr = "Simplifica proceso, agrega prueba social y propuesta de valor."
        elif cr < 5:
            nivel_cr = "ACEPTABLE"
            msg_cr = "Haz A/B testing de titulares y diferentes CTAs."
        elif cr <= 10:
            nivel_cr = "BUENO"
            msg_cr = "Escala tráfico y documenta éxitos."
        else:
            nivel_cr = "EXCELENTE"
            msg_cr = "Maximiza tráfico y aumenta ticket promedio."
        analisis.append(f"Conv: {nivel_cr} ({round(cr, 2)}%). {msg_cr}")

        if growth <= 0:
            nivel_growth = "ESTANCADO"
            alertas.append(f"CRECIMIENTO ESTANCADO: {round(growth, 1)}%.")
            msg_growth = "Rota creativos, amplía segmentación y sube puja."
        elif growth <= 5:
            nivel_growth = "LENTO"
            msg_growth = "Prueba nuevos copies y audiencias lookalike."
        else:
            nivel_growth = "SALUDABLE"
            msg_growth = "Estrategia sólida. Monitorea que el CPC no suba."
        analisis.append(f"Crecimiento: {nivel_growth} ({round(growth, 1)}%). {msg_growth}")

        if alertas or roi_pesos < 200000:
            title = f"Análisis: {camp['name']}"
            priority_msg = "\n".join(alertas) if alertas else ""
            full_msg = (priority_msg + "\n\n" + "\n".join(analisis)).strip()
            tipo = 'warning' if (alertas or roi_pesos < 0) else 'recommendation'
            _create_unique_notification(id_user, title, full_msg, tipo)
        
        # Alerta de presupuesto
        check_campaign_budget_alerts(id_user, cid)

def check_campaign_budget_alerts(id_user: int, id_campaign: int):
    """
    Verifica si una campaña ha alcanzado el 80% o el 100% de su presupuesto.
    """
    camp = run_query(
        "SELECT name, spent, budget FROM campaigns WHERE id_campaign = %s",
        (id_campaign,), fetch=True
    )
    if not camp: return
    
    camp = camp[0]
    spent = float(camp['spent'] or 0)
    budget = float(camp['budget'] or 0)
    
    if budget <= 0: return

    if spent >= budget:
        title = "🔴 PRESUPUESTO AGOTADO"
        msg = f"La campaña '{camp['name']}' ha alcanzado el 100% de su presupuesto (${budget}). Se recomienda pausarla o aumentar los fondos."
        _create_unique_notification(id_user, title, msg, "error")
    elif spent >= budget * 0.8:
        title = "🟡 ALERTA DE PRESUPUESTO"
        msg = f"La campaña '{camp['name']}' ha consumido el 80% de su presupuesto (${spent}/${budget})."
        _create_unique_notification(id_user, title, msg, "warning")

def export_conversions_csv_service(id_company: int):
    """
    Genera un string en formato CSV con todas las conversiones de una empresa.
    """
    conversions = run_query("""
        SELECT cv.id_conversion, cv.revenue, cv.type, cv.notes, cv.created_at,
               ck.ip_address_hash as ip, ck.country, ck.utm_source, ck.utm_medium, ck.utm_campaign
        FROM conversions cv
        JOIN clicks ck ON cv.id_click = ck.id_click
        JOIN tracking_links tl ON ck.id_link = tl.id_link
        WHERE tl.id_campaign IN (SELECT id_campaign FROM campaigns WHERE id_company = %s)
        ORDER BY cv.created_at DESC
    """, (id_company,), fetch=True)
    
    if not conversions:
        return "ID,Revenue,Type,Notes,Date,Country,Source,Medium,Campaign\n"
    
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Revenue", "Type", "Notes", "Date", "Country", "Source", "Medium", "Campaign"])
    
    for c in conversions:
        writer.writerow([
            c['id_conversion'],
            c['revenue'],
            c['type'],
            c['notes'],
            c['created_at'].isoformat() if c['created_at'] else "",
            c['country'] or "N/A",
            c['utm_source'] or "N/A",
            c['utm_medium'] or "N/A",
            c['utm_campaign'] or "N/A"
        ])
    
    return output.getvalue()

def _create_unique_notification(id_user: int, title: str, message: str, type: str):
    existe = run_query(
        "SELECT id_notification FROM notifications WHERE id_user=%s AND title=%s AND message=%s AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)",
        (id_user, title, message), fetch=True
    )
    if not existe:
        run_query(
            "INSERT INTO notifications (id_user, title, message, type) VALUES (%s, %s, %s, %s)",
            (id_user, title, message, type)
        )



# ---------------------------------------------------------------
# PERSONS
# ---------------------------------------------------------------
def insert_person(data: Person):
    try:
        return run_query(
            "INSERT INTO persons (name, lastname, email, phone) VALUES (%s, %s, %s, %s)",
            (data.name, data.lastname, data.email, data.phone),
            return_lastrowid=True
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar persona: {e}")

def update_person_service(id_person: int, data: Person):
    try:
        run_query(
            "UPDATE persons SET name=%s, lastname=%s, email=%s, phone=%s WHERE id_person=%s",
            (data.name, data.lastname, data.email, data.phone, id_person)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar persona: {e}")

def delete_person_service(id_person: int):
    try:
        run_query("DELETE FROM persons WHERE id_person=%s", (id_person,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar la persona: {e}")


# ---------------------------------------------------------------
# ROLE
# ---------------------------------------------------------------
def insert_role(data: Role):
    try:
        run_query("INSERT INTO role (name) VALUES (%s)", (data.name,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar rol: {e}")

def update_role_service(id_role: int, data: Role):
    try:
        run_query("UPDATE role SET name=%s WHERE id_role=%s", (data.name, id_role))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar rol: {e}")

def delete_role_service(id_role: int):
    try:
        run_query("DELETE FROM role WHERE id_role=%s", (id_role,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el rol: {e}")


# ---------------------------------------------------------------
# PERMISSIONS
# ---------------------------------------------------------------
def insert_permission(data: Permission):
    try:
        run_query(
            "INSERT INTO permissions (name, description) VALUES (%s, %s)",
            (data.name, data.description)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar permiso: {e}")

def update_permission_service(id_permissions: int, data: Permission):
    try:
        run_query(
            "UPDATE permissions SET name=%s, description=%s WHERE id_permissions=%s",
            (data.name, data.description, id_permissions)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar permiso: {e}")

def delete_permission_service(id_permissions: int):
    try:
        run_query("DELETE FROM permissions WHERE id_permissions=%s", (id_permissions,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el permiso: {e}")


# ---------------------------------------------------------------
# ROLE_HAS_PERMISSIONS
# ---------------------------------------------------------------
def insert_role_permission(data: RoleHasPermission):
    try:
        run_query(
            "INSERT INTO role_has_permissions (id_role, id_permission) VALUES (%s, %s)",
            (data.id_role, data.id_permission)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al asignar permiso al rol: {e}")

def delete_role_permission_service(id_role_permission: int):
    run_query(
        "DELETE FROM role_has_permissions WHERE id_role_permission=%s",
        (id_role_permission,)
    )


# ---------------------------------------------------------------
# COMPANIES
# ---------------------------------------------------------------
def insert_company(data: Company):
    try:
        # Insertar empresa
        id_company = run_query(
            "INSERT INTO companies (id_user, name) VALUES (%s, %s)",
            (data.id_user, data.name),
            return_lastrowid=True
        )
        # Crear relación en tabla intermedia
        if data.id_user:
            run_query(
                "INSERT INTO user_company (id_user, id_company) VALUES (%s, %s)",
                (data.id_user, id_company)
            )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar empresa: {e}")

def update_company_service(id_company: int, data: Company):
    try:
        run_query(
            "UPDATE companies SET id_user=%s, name=%s WHERE id_company=%s",
            (data.id_user, data.name, id_company)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar empresa: {e}")

def delete_company_service(id_company: int):
    try:
        run_query("DELETE FROM companies WHERE id_company=%s", (id_company,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar la empresa: {e}")


# ---------------------------------------------------------------
# USERS
# ---------------------------------------------------------------
def insert_user(data: User):
    try:
        password_hash = hash_password(data.password_hash)
        # CORRECCIÓN: id_company no va en INSERT; username es requerido (NOT NULL UNIQUE)
        # Se usa la parte local del email de la persona como username
        person_row = run_query(
            "SELECT email FROM persons WHERE id_person=%s", (data.id_person,), fetch=True
        )
        email_val = person_row[0]['email'] if person_row else str(data.id_person)
        username = email_val.split('@')[0]
        id_user = run_query(
            "INSERT INTO users (id_person, id_role, username, password_hash) VALUES (%s, %s, %s, %s)",
            (data.id_person, data.id_role, username, password_hash),
            return_lastrowid=True
        )
        if data.id_company is not None:
            run_query(
                "INSERT INTO user_company (id_user, id_company) VALUES (%s, %s)",
                (id_user, data.id_company)
            )
        return id_user
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar usuario: {e}")

def update_user_service(id_user: int, data: User):
    try:
        # Evitar doble hash: verificar si ya es un hash bcrypt válido
        if data.password_hash:
            if not is_bcrypt_hash(data.password_hash):
                password_hash = hash_password(data.password_hash)
            else:
                password_hash = data.password_hash
        else:
            password_hash = data.password_hash
        
        run_query(
            "UPDATE users SET id_person=%s, id_role=%s, password_hash=%s WHERE id_user=%s",
            (data.id_person, data.id_role, password_hash, id_user)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar usuario: {e}")

def delete_user_service(id_user: int):
    try:
        run_query("DELETE FROM companies WHERE id_user=%s", (id_user,))
        run_query("DELETE FROM users WHERE id_user=%s", (id_user,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el usuario: {e}")


# ---------------------------------------------------------------
# USER_COMPANY
# ---------------------------------------------------------------
def insert_user_company(data: UserCompany):
    try:
        run_query(
            "INSERT INTO user_company (id_user, id_company) VALUES (%s, %s)",
            (data.id_user, data.id_company)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al asociar usuario a empresa: {e}")

def delete_user_company_service(id_user_company: int):
    run_query(
        "DELETE FROM user_company WHERE id_user_company=%s",
        (id_user_company,)
    )


# ---------------------------------------------------------------
# CAMPAIGNS
# ---------------------------------------------------------------
def insert_campaign(data: Campaign):
    try:
        return run_query(
            "INSERT INTO campaigns (id_company, name, description, status, start_date, end_date, spent, budget) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data.id_company, data.name, data.description, data.status, data.start_date, data.end_date, data.spent, data.budget),
            return_lastrowid=True
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar campaña: {e}")

def update_campaign_service(id_campaign: int, data: Campaign):
    try:
        run_query(
            "UPDATE campaigns SET id_company=%s, name=%s, description=%s, status=%s, start_date=%s, end_date=%s, spent=%s, budget=%s WHERE id_campaign=%s",
            (data.id_company, data.name, data.description, data.status, data.start_date, data.end_date, data.spent, data.budget, id_campaign)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar campaña: {e}")

def delete_campaign_service(id_campaign: int):
    try:
        run_query("DELETE FROM campaigns WHERE id_campaign=%s", (id_campaign,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar la campaña: {e}")


# ---------------------------------------------------------------
# CHANNELS
# ---------------------------------------------------------------
def insert_channel(data: Channel):
    try:
        run_query(
            "INSERT INTO channels (name, description) VALUES (%s, %s)",
            (data.name, data.description)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar canal: {e}")

def update_channel_service(id_channel: int, data: Channel):
    try:
        run_query(
            "UPDATE channels SET name=%s, description=%s WHERE id_channel=%s",
            (data.name, data.description, id_channel)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar canal: {e}")

def delete_channel_service(id_channel: int):
    try:
        run_query("DELETE FROM channels WHERE id_channel=%s", (id_channel,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el canal: {e}")


# ---------------------------------------------------------------
# TRACKING LINKS
# ---------------------------------------------------------------
def insert_tracking_link(data: TrackingLink):
    try:
        return run_query(
            "INSERT INTO tracking_links (id_campaign, id_channel, destination) VALUES (%s, %s, %s)",
            (data.id_campaign, data.id_channel, data.destination),
            return_lastrowid=True
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar tracking link: {e}")

def update_tracking_link_service(id_link: int, data: TrackingLink):
    try:
        run_query(
            "UPDATE tracking_links SET id_campaign=%s, id_channel=%s, destination=%s WHERE id_link=%s",
            (data.id_campaign, data.id_channel, data.destination, id_link)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar tracking link: {e}")

def delete_tracking_link_service(id_link: int):
    try:
        run_query("DELETE FROM tracking_links WHERE id_link=%s", (id_link,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el tracking link: {e}")


# ---------------------------------------------------------------
# CLICKS
# ---------------------------------------------------------------
def insert_click(data: Click):
    try:
        run_query(
            """INSERT INTO clicks (
                id_link, ip_address_hash, consent_given, user_agent, referrer, country, 
                utm_source, utm_medium, utm_campaign, utm_term, utm_content, clicked_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data.id_link, data.ip_address_hash, data.consent_given, data.user_agent, 
                data.referrer, data.country, data.utm_source, data.utm_medium, 
                data.utm_campaign, data.utm_term, data.utm_content, data.clicked_at
            )
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar click: {e}")

def update_click_service(id_click: int, data: Click):
    try:
        run_query(
            """UPDATE clicks SET 
                id_link=%s, ip_address_hash=%s, consent_given=%s, user_agent=%s, referrer=%s, country=%s, 
                utm_source=%s, utm_medium=%s, utm_campaign=%s, utm_term=%s, utm_content=%s, clicked_at=%s 
            WHERE id_click=%s""",
            (
                data.id_link, data.ip_address_hash, data.consent_given, data.user_agent, 
                data.referrer, data.country, data.utm_source, data.utm_medium, 
                data.utm_campaign, data.utm_term, data.utm_content, data.clicked_at, id_click
            )
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar click: {e}")

def delete_click_service(id_click: int):
    try:
        run_query("DELETE FROM clicks WHERE id_click=%s", (id_click,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar el click: {e}")


# ---------------------------------------------------------------
# CONVERSIONS
# ---------------------------------------------------------------
def insert_conversion(data: Conversion):
    try:
        run_query(
            "INSERT INTO conversions (id_click, revenue, type, source, notes) VALUES (%s, %s, %s, %s, %s)",
            (data.id_click, float(data.revenue), data.type, data.source, data.notes)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar conversión: {e}")

def update_conversion_service(id_conversion: int, data: Conversion):
    try:
        run_query(
            "UPDATE conversions SET id_click=%s, revenue=%s, type=%s, source=%s, notes=%s WHERE id_conversion=%s",
            (data.id_click, float(data.revenue), data.type, data.source, data.notes, id_conversion)
        )
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar conversión: {e}")

def delete_conversion_service(id_conversion: int):
    try:
        run_query("DELETE FROM conversions WHERE id_conversion=%s", (id_conversion,))
    except pymysql.err.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar la conversión: {e}")


# ---------------------------------------------------------------
# AUTHORIZATION HELPERS
# ---------------------------------------------------------------
def build_in_clause(values: list[int]) -> tuple[str, tuple]:
    placeholders = ", ".join(["%s"] * len(values))
    return f"({placeholders})", tuple(values)


def get_user_company_ids(id_user: int, id_role: int = None) -> list[int]:
    # Si es Super Admin, retornar todas las empresas
    if id_role == 1:
        all_companies = run_query("SELECT id_company FROM companies", fetch=True)
        return [c["id_company"] for c in all_companies]

    # Buscar en tabla intermedia user_company
    rows = run_query(
        "SELECT id_company FROM user_company WHERE id_user=%s",
        (id_user,),
        fetch=True
    )
    company_ids = [row["id_company"] for row in rows]
    
    # También buscar en tabla companies (por si el usuario es propietario directo)
    company_owner_rows = run_query(
        "SELECT id_company FROM companies WHERE id_user=%s",
        (id_user,),
        fetch=True
    )
    owner_company_ids = [row["id_company"] for row in company_owner_rows]
    
    # Combinar y eliminar duplicados
    all_company_ids = list(set(company_ids + owner_company_ids))
    return all_company_ids


def ensure_company_access(id_user: int, id_company: int, id_role: int = None) -> None:
    if id_role == 1: return
    company_ids = get_user_company_ids(id_user, id_role)
    if id_company not in company_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")


def ensure_campaign_access(id_user: int, id_campaign: int, id_role: int = None) -> None:
    if id_role == 1: return
    result = run_query(
        "SELECT id_company FROM campaigns WHERE id_campaign=%s",
        (id_campaign,),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaña no encontrada")
    ensure_company_access(id_user, result[0]["id_company"], id_role)


def ensure_tracking_link_access(id_user: int, id_link: int, id_role: int = None) -> None:
    if id_role == 1: return
    result = run_query(
        """
        SELECT c.id_company
        FROM tracking_links tl
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE tl.id_link=%s
        """,
        (id_link,),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracking link no encontrado")
    ensure_company_access(id_user, result[0]["id_company"], id_role)


def ensure_click_access(id_user: int, id_click: int, id_role: int = None) -> None:
    if id_role == 1: return
    result = run_query(
        """
        SELECT c.id_company
        FROM clicks ck
        JOIN tracking_links tl ON ck.id_link = tl.id_link
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE ck.id_click=%s
        """,
        (id_click,),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Click no encontrado")
    ensure_company_access(id_user, result[0]["id_company"], id_role)


def ensure_conversion_access(id_user: int, id_conversion: int, id_role: int = None) -> None:
    if id_role == 1: return
    # CORRECCIÓN: conversions NO tiene columna id_campaign directa.
    # Se obtiene id_company a través de clicks → tracking_links → campaigns.
    result = run_query(
        """
        SELECT c.id_company
        FROM conversions cv
        JOIN clicks ck ON cv.id_click = ck.id_click
        JOIN tracking_links tl ON ck.id_link = tl.id_link
        JOIN campaigns c ON tl.id_campaign = c.id_campaign
        WHERE cv.id_conversion=%s
        """,
        (id_conversion,),
        fetch=True
    )
    if not result or result[0]["id_company"] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversión no encontrada")
    ensure_company_access(id_user, result[0]["id_company"], id_role)


def ensure_person_access(id_user: int, id_person: int, id_role: int = None) -> None:
    if id_role == 1: return
    company_ids = get_user_company_ids(id_user, id_role)
    if not company_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    in_clause, params = build_in_clause(company_ids)
    result = run_query(
        f"""
        SELECT p.id_person
        FROM persons p
        JOIN users u ON p.id_person = u.id_person
        JOIN user_company uc ON u.id_user = uc.id_user
        WHERE p.id_person=%s AND uc.id_company IN {in_clause}
        """,
        (id_person, *params),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")


def ensure_user_access(id_user: int, target_user_id: int, id_role: int = None) -> None:
    if id_role == 1 or id_user == target_user_id:
        return
    company_ids = get_user_company_ids(id_user, id_role)
    if not company_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    in_clause, params = build_in_clause(company_ids)
    result = run_query(
        f"""
        SELECT u.id_user
        FROM users u
        JOIN user_company uc ON u.id_user = uc.id_user
        WHERE u.id_user=%s AND uc.id_company IN {in_clause}
        """,
        (target_user_id, *params),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")


def ensure_user_company_access(id_user: int, id_user_company: int, id_role: int = None) -> None:
    if id_role == 1: return
    company_ids = get_user_company_ids(id_user, id_role)
    if not company_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    in_clause, params = build_in_clause(company_ids)
    result = run_query(
        f"""
        SELECT id_user_company
        FROM user_company
        WHERE id_user_company=%s AND id_company IN {in_clause}
        """,
        (id_user_company, *params),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")


# ---------------------------------------------------------------
# READ TABLE
# ---------------------------------------------------------------
def read_table_for_user(table: str, id_user: int, id_role: int = None):
    allowed_tables = {
        "persons", "role", "permissions", "role_has_permissions",
        "companies", "users", "user_company",
        "campaigns", "channels", "tracking_links", "clicks", "conversions"
    }
    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Tabla '{table}' no permitida")

    company_ids = get_user_company_ids(id_user, id_role)
    if not company_ids and id_role != 1 and table in {
        "persons", "companies", "users", "user_company",
        "campaigns", "tracking_links", "clicks", "conversions"
    }:
        return []

    if table in {"role", "permissions", "role_has_permissions", "channels"}:
        return read_table(table)

    in_clause, params = build_in_clause(company_ids) if company_ids else ("(%s)", tuple())

    if table == "companies":
        query = "SELECT * FROM companies"
        if id_role != 1:
            query += f" WHERE id_company IN {in_clause}"
        query += " ORDER BY id_company"
        return run_query(query, params if id_role != 1 else (), fetch=True)

    if table == "users":
        if id_role == 1:
            return run_query("""
                SELECT u.*, p.name, p.lastname, p.email 
                FROM users u 
                JOIN persons p ON u.id_person = p.id_person 
                ORDER BY u.id_user
            """, fetch=True)
        return run_query(
            f"""
            SELECT DISTINCT u.*, p.name, p.lastname, p.email
            FROM users u
            JOIN persons p ON u.id_person = p.id_person
            JOIN user_company uc ON u.id_user = uc.id_user
            WHERE uc.id_company IN {in_clause}
            ORDER BY u.id_user
            """,
            params,
            fetch=True
        )

    if table == "user_company":
        if id_role == 1:
            return run_query("SELECT * FROM user_company ORDER BY id_user_company", fetch=True)
        return run_query(
            "SELECT * FROM user_company WHERE id_user = %s ORDER BY id_user_company",
            (id_user,),
            fetch=True
        )

    if table == "persons":
        if id_role == 1:
            return run_query("SELECT * FROM persons ORDER BY id_person", fetch=True)
        return run_query(
            f"""
            SELECT DISTINCT p.*
            FROM persons p
            JOIN users u ON p.id_person = u.id_person
            JOIN user_company uc ON u.id_user = uc.id_user
            WHERE uc.id_company IN {in_clause}
            ORDER BY p.id_person
            """,
            params,
            fetch=True
        )

    if table == "campaigns":
        query = "SELECT * FROM campaigns"
        if id_role != 1:
            query += f" WHERE id_company IN {in_clause}"
        query += " ORDER BY id_campaign"
        return run_query(query, params if id_role != 1 else (), fetch=True)

    if table == "tracking_links":
        if id_role == 1:
            return run_query("SELECT * FROM tracking_links ORDER BY id_link", fetch=True)
        return run_query(
            f"""
            SELECT tl.*
            FROM tracking_links tl
            JOIN campaigns c ON tl.id_campaign = c.id_campaign
            WHERE c.id_company IN {in_clause}
            ORDER BY tl.id_link
            """,
            params,
            fetch=True
        )

    if table == "clicks":
        if id_role == 1:
            return run_query("SELECT * FROM clicks ORDER BY id_click", fetch=True)
        return run_query(
            f"""
            SELECT ck.*
            FROM clicks ck
            JOIN tracking_links tl ON ck.id_link = tl.id_link
            JOIN campaigns c ON tl.id_campaign = c.id_campaign
            WHERE c.id_company IN {in_clause}
            ORDER BY ck.id_click
            """,
            params,
            fetch=True
        )

    if table == "conversions":
        if id_role == 1:
            return run_query("SELECT * FROM conversions ORDER BY id_conversion", fetch=True)
        return run_query(
            f"""
            SELECT cv.*
            FROM conversions cv
            JOIN clicks ck ON cv.id_click = ck.id_click
            JOIN tracking_links tl ON ck.id_link = tl.id_link
            JOIN campaigns c ON tl.id_campaign = c.id_campaign
            WHERE c.id_company IN {in_clause}
            ORDER BY cv.id_conversion
            """,
            params,
            fetch=True
        )

    return read_table(table)


def read_table(table: str):
    allowed_tables = {
        "persons", "role", "permissions", "role_has_permissions",
        "companies", "users", "user_company",
        "campaigns", "channels", "tracking_links", "clicks", "conversions"
    }
    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Tabla '{table}' no permitida")

    id_column_map = {
        "persons":               "id_person",
        "role":                  "id_role",
        "permissions":           "id_permissions",
        "role_has_permissions":  "id_role_permission",
        "companies":             "id_company",
        "users":                 "id_user",
        "user_company":          "id_user_company",
        "campaigns":             "id_campaign",
        "channels":              "id_channel",
        "tracking_links":        "id_link",
        "clicks":                "id_click",
        "conversions":           "id_conversion",
    }
    id_col = id_column_map[table]

    return run_query(f"SELECT * FROM {table} ORDER BY {id_col}", fetch=True)
# ---------------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------------
def get_user_notifications(id_user: int):
    # Primero generamos recomendaciones automáticas si es necesario
    generate_auto_recommendations(id_user)
    
    return run_query(
        "SELECT * FROM notifications WHERE id_user = %s ORDER BY created_at DESC LIMIT 50",
        (id_user,),
        fetch=True
    )

def mark_notification_read(id_notification: int):
    run_query(
        "UPDATE notifications SET is_read = TRUE WHERE id_notification = %s",
        (id_notification,)
    )

def get_unread_count_service(id_user: int):
    """
    Retorna el conteo de notificaciones no leídas para un usuario.
    """
    result = run_query(
        "SELECT COUNT(*) as unread_count FROM notifications WHERE id_user = %s AND is_read = FALSE",
        (id_user,),
        fetch=True
    )
    return result[0]['unread_count'] if result else 0


