from fastapi import APIRouter, Depends, HTTPException, status

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

from app.services.a_service import *
from app.security import get_current_user

router = APIRouter(prefix="/analitika", tags=["Analitika"])

@router.get("/")
def root(current_user: dict = Depends(get_current_user)):
    return {"message": "API conectada a analitika_db"}


# PERSONS ----------------

@router.post("/persons")
def create_person(data: Person, current_user: dict = Depends(get_current_user)):
    insert_person(data)
    return {"ok": True}

@router.get("/persons")
def get_persons(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("persons", current_user["id_user"])

@router.put("/persons/{id}")
def update_person(id: int, data: Person, current_user: dict = Depends(get_current_user)):
    ensure_person_access(current_user["id_user"], id)
    update_person_service(id, data)
    return {"ok": True}

@router.delete("/persons/{id}")
def delete_person(id: int, current_user: dict = Depends(get_current_user)):
    ensure_person_access(current_user["id_user"], id)
    delete_person_service(id)
    return {"ok": True}


# ROLE ----------------

@router.post("/roles")
def create_role(data: Role, current_user: dict = Depends(get_current_user)):
    insert_role(data)
    return {"ok": True}

@router.get("/roles")
def get_roles(current_user: dict = Depends(get_current_user)):
    return read_table("role")

@router.put("/roles/{id}")
def update_role(id: int, data: Role, current_user: dict = Depends(get_current_user)):
    update_role_service(id, data)
    return {"ok": True}

@router.delete("/roles/{id}")
def delete_role(id: int, current_user: dict = Depends(get_current_user)):
    delete_role_service(id)
    return {"ok": True}


# PERMISSIONS ----------------

@router.post("/permissions")
def create_permission(data: Permission, current_user: dict = Depends(get_current_user)):
    insert_permission(data)
    return {"ok": True}

@router.get("/permissions")
def get_permissions(current_user: dict = Depends(get_current_user)):
    return read_table("permissions")

@router.put("/permissions/{id}")
def update_permission(id: int, data: Permission, current_user: dict = Depends(get_current_user)):
    update_permission_service(id, data)
    return {"ok": True}

@router.delete("/permissions/{id}")
def delete_permission(id: int, current_user: dict = Depends(get_current_user)):
    delete_permission_service(id)
    return {"ok": True}


# ROLE_HAS_PERMISSIONS ----------------

@router.post("/role-permissions")
def create_role_permission(data: RoleHasPermission, current_user: dict = Depends(get_current_user)):
    insert_role_permission(data)
    return {"ok": True}

@router.get("/role-permissions")
def get_role_permissions(current_user: dict = Depends(get_current_user)):
    return read_table("role_has_permissions")

@router.delete("/role-permissions/{id}")
def delete_role_permission(id: int, current_user: dict = Depends(get_current_user)):
    delete_role_permission_service(id)
    return {"ok": True}


# COMPANIES ----------------

@router.post("/companies")
def create_company(data: Company, current_user: dict = Depends(get_current_user)):
    if data.id_user is not None and data.id_user != current_user["id_user"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    insert_company(data)
    return {"ok": True}

@router.get("/companies")
def get_companies(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("companies", current_user["id_user"])

@router.put("/companies/{id}")
def update_company(id: int, data: Company, current_user: dict = Depends(get_current_user)):
    ensure_company_access(current_user["id_user"], id)
    update_company_service(id, data)
    return {"ok": True}

@router.delete("/companies/{id}")
def delete_company(id: int, current_user: dict = Depends(get_current_user)):
    ensure_company_access(current_user["id_user"], id)
    delete_company_service(id)
    return {"ok": True}


# USERS ----------------

@router.post("/users")
def create_user(data: User, current_user: dict = Depends(get_current_user)):
    if data.id_company is not None:
        ensure_company_access(current_user["id_user"], data.id_company)
    insert_user(data)
    return {"ok": True}

@router.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    rows = read_table_for_user("users", current_user["id_user"])
    return [
        {k: v for k, v in row.items() if k != "password_hash"}
        for row in rows
    ]

@router.put("/users/{id}")
def update_user(id: int, data: User, current_user: dict = Depends(get_current_user)):
    if data.id_company is not None:
        ensure_company_access(current_user["id_user"], data.id_company)
    update_user_service(id, data)
    return {"ok": True}

@router.delete("/users/{id}")
def delete_user(id: int, current_user: dict = Depends(get_current_user)):
    ensure_user_access(current_user["id_user"], id)
    delete_user_service(id)
    return {"ok": True}


# USER_COMPANY ----------------

@router.post("/user-company")
def create_user_company(data: UserCompany, current_user: dict = Depends(get_current_user)):
    ensure_company_access(current_user["id_user"], data.id_company)
    insert_user_company(data)
    return {"ok": True}

@router.get("/user-company")
def get_user_company(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("user_company", current_user["id_user"])

@router.delete("/user-company/{id}")
def delete_user_company(id: int, current_user: dict = Depends(get_current_user)):
    ensure_user_company_access(current_user["id_user"], id)
    delete_user_company_service(id)
    return {"ok": True}


# CAMPAIGNS ----------------

@router.post("/campaigns")
def create_campaign(data: Campaign, current_user: dict = Depends(get_current_user)):
    ensure_company_access(current_user["id_user"], data.id_company)
    id_campaign = insert_campaign(data)
    return {"ok": True, "id_campaign": id_campaign}

@router.get("/campaigns")
def get_campaigns(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("campaigns", current_user["id_user"])

@router.put("/campaigns/{id}")
def update_campaign(id: int, data: Campaign, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id)
    update_campaign_service(id, data)
    return {"ok": True}

@router.delete("/campaigns/{id}")
def delete_campaign(id: int, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], id)
    delete_campaign_service(id)
    return {"ok": True}


# CHANNELS ----------------

@router.post("/channels")
def create_channel(data: Channel, current_user: dict = Depends(get_current_user)):
    insert_channel(data)
    return {"ok": True}

@router.get("/channels")
def get_channels(current_user: dict = Depends(get_current_user)):
    return read_table("channels")

@router.put("/channels/{id}")
def update_channel(id: int, data: Channel, current_user: dict = Depends(get_current_user)):
    update_channel_service(id, data)
    return {"ok": True}

@router.delete("/channels/{id}")
def delete_channel(id: int, current_user: dict = Depends(get_current_user)):
    delete_channel_service(id)
    return {"ok": True}


# TRACKING LINKS ----------------

@router.post("/tracking-links")
def create_tracking_link(data: TrackingLink, current_user: dict = Depends(get_current_user)):
    ensure_campaign_access(current_user["id_user"], data.id_campaign)
    id_link = insert_tracking_link(data)
    return {"ok": True, "id_link": id_link}

@router.get("/tracking-links")
def get_tracking_links(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("tracking_links", current_user["id_user"])

@router.put("/tracking-links/{id}")
def update_tracking_link(id: int, data: TrackingLink, current_user: dict = Depends(get_current_user)):
    ensure_tracking_link_access(current_user["id_user"], id)
    update_tracking_link_service(id, data)
    return {"ok": True}

@router.delete("/tracking-links/{id}")
def delete_tracking_link(id: int, current_user: dict = Depends(get_current_user)):
    ensure_tracking_link_access(current_user["id_user"], id)
    delete_tracking_link_service(id)
    return {"ok": True}


# CLICKS ----------------

@router.post("/clicks")
def create_click(data: Click, current_user: dict = Depends(get_current_user)):
    ensure_tracking_link_access(current_user["id_user"], data.id_link)
    insert_click(data)
    return {"ok": True}

@router.get("/clicks")
def get_clicks(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("clicks", current_user["id_user"])

@router.put("/clicks/{id}")
def update_click(id: int, data: Click, current_user: dict = Depends(get_current_user)):
    ensure_click_access(current_user["id_user"], id)
    update_click_service(id, data)
    return {"ok": True}

@router.delete("/clicks/{id}")
def delete_click(id: int, current_user: dict = Depends(get_current_user)):
    ensure_click_access(current_user["id_user"], id)
    delete_click_service(id)
    return {"ok": True}


# CONVERSIONS ----------------

@router.post("/conversions")
def create_conversion(data: Conversion, current_user: dict = Depends(get_current_user)):
    ensure_click_access(current_user["id_user"], data.id_click)
    insert_conversion(data)
    return {"ok": True}

@router.get("/conversions")
def get_conversions(current_user: dict = Depends(get_current_user)):
    return read_table_for_user("conversions", current_user["id_user"])

@router.put("/conversions/{id}")
def update_conversion(id: int, data: Conversion, current_user: dict = Depends(get_current_user)):
    ensure_conversion_access(current_user["id_user"], id)
    update_conversion_service(id, data)
    return {"ok": True}

@router.delete("/conversions/{id}")
def delete_conversion(id: int, current_user: dict = Depends(get_current_user)):
    ensure_conversion_access(current_user["id_user"], id)
    delete_conversion_service(id)
    return {"ok": True}


# ANALYTICS ----------------

@router.get("/campaigns/top")
def get_top_campaigns(limit: int = 5, current_user: dict = Depends(get_current_user)):
    company_ids = get_user_company_ids(current_user["id_user"])
    if not company_ids:
        return []
    in_clause, params = build_in_clause(company_ids)
    resultado = run_query(f"""
        SELECT c.id_campaign, c.name, 
               COUNT(cl.id_click) as clics,
               COALESCE(SUM(cv.revenue), 0) as ingresos,
               c.spent,
               COALESCE(SUM(cv.revenue), 0) - c.spent as beneficio
        FROM campaigns c
        LEFT JOIN tracking_links tl ON c.id_campaign = tl.id_campaign
        LEFT JOIN clicks cl ON tl.id_link = cl.id_link
        LEFT JOIN conversions cv ON cl.id_click = cv.id_click
        WHERE c.id_company IN {in_clause}
        GROUP BY c.id_campaign
        ORDER BY clics DESC
        LIMIT %s
    """, (*params, limit), fetch=True)
    return resultado

# NOTIFICATIONS ----------------
@router.get("/notifications")
@router.get("/notifications/")
def get_notifications(current_user: dict = Depends(get_current_user)):
    return get_user_notifications(current_user["id_user"])

@router.get("/notifications/unread-count")
@router.get("/notifications/unread-count/")
def get_unread_count(current_user: dict = Depends(get_current_user)):
    return {"count": get_unread_count_service(current_user["id_user"])}

@router.put("/notifications/{id}/read")
@router.put("/notifications/{id}/read/")
def mark_read(id: int, current_user: dict = Depends(get_current_user)):
    mark_notification_read(id)
    return {"ok": True}

