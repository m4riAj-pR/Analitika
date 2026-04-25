from fastapi import APIRouter

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

router = APIRouter(prefix="/analitika", tags=["Analitika"])

VALID_TABLES = {
    "persons", "role", "permissions", "role_has_permissions",
    "companies", "users", "user_company",
    "campaigns", "channels", "tracking_links", "clicks", "conversions"
}

@router.get("/")
def root():
    return {"message": "API conectada a analitika_db"}


# PERSONS ----------------

@router.post("/persons")
def create_person(data: Person):
    insert_person(data)
    return {"ok": True}

@router.get("/persons")
def get_persons():
    return read_table("persons")

@router.put("/persons/{id}")
def update_person(id: int, data: Person):
    update_person_service(id, data)
    return {"ok": True}

@router.delete("/persons/{id}")
def delete_person(id: int):
    delete_person_service(id)
    return {"ok": True}


# ROLE ----------------

@router.post("/roles")
def create_role(data: Role):
    insert_role(data)
    return {"ok": True}

@router.get("/roles")
def get_roles():
    return read_table("role")

@router.put("/roles/{id}")
def update_role(id: int, data: Role):
    update_role_service(id, data)
    return {"ok": True}

@router.delete("/roles/{id}")
def delete_role(id: int):
    delete_role_service(id)
    return {"ok": True}


# PERMISSIONS ----------------

@router.post("/permissions")
def create_permission(data: Permission):
    insert_permission(data)
    return {"ok": True}

@router.get("/permissions")
def get_permissions():
    return read_table("permissions")

@router.put("/permissions/{id}")
def update_permission(id: int, data: Permission):
    update_permission_service(id, data)
    return {"ok": True}

@router.delete("/permissions/{id}")
def delete_permission(id: int):
    delete_permission_service(id)
    return {"ok": True}


# ROLE_HAS_PERMISSIONS ----------------

@router.post("/role-permissions")
def create_role_permission(data: RoleHasPermission):
    insert_role_permission(data)
    return {"ok": True}

@router.get("/role-permissions")
def get_role_permissions():
    return read_table("role_has_permissions")

@router.delete("/role-permissions/{id}")
def delete_role_permission(id: int):
    delete_role_permission_service(id)
    return {"ok": True}


# COMPANIES ----------------

@router.post("/companies")
def create_company(data: Company):
    insert_company(data)
    return {"ok": True}

@router.get("/companies")
def get_companies():
    return read_table("companies")

@router.put("/companies/{id}")
def update_company(id: int, data: Company):
    update_company_service(id, data)
    return {"ok": True}

@router.delete("/companies/{id}")
def delete_company(id: int):
    delete_company_service(id)
    return {"ok": True}


# USERS ----------------

@router.post("/users")
def create_user(data: User):
    insert_user(data)
    return {"ok": True}

@router.get("/users")
def get_users():
    return read_table("users")

@router.put("/users/{id}")
def update_user(id: int, data: User):
    update_user_service(id, data)
    return {"ok": True}

@router.delete("/users/{id}")
def delete_user(id: int):
    delete_user_service(id)
    return {"ok": True}


# USER_COMPANY ----------------

@router.post("/user-company")
def create_user_company(data: UserCompany):
    insert_user_company(data)
    return {"ok": True}

@router.get("/user-company")
def get_user_company():
    return read_table("user_company")

@router.delete("/user-company/{id}")
def delete_user_company(id: int):
    delete_user_company_service(id)
    return {"ok": True}


# CAMPAIGNS ----------------

@router.post("/campaigns")
def create_campaign(data: Campaign):
    insert_campaign(data)
    return {"ok": True}

@router.get("/campaigns")
def get_campaigns():
    return read_table("campaigns")

@router.put("/campaigns/{id}")
def update_campaign(id: int, data: Campaign):
    update_campaign_service(id, data)
    return {"ok": True}

@router.delete("/campaigns/{id}")
def delete_campaign(id: int):
    delete_campaign_service(id)
    return {"ok": True}


# CHANNELS ----------------

@router.post("/channels")
def create_channel(data: Channel):
    insert_channel(data)
    return {"ok": True}

@router.get("/channels")
def get_channels():
    return read_table("channels")

@router.put("/channels/{id}")
def update_channel(id: int, data: Channel):
    update_channel_service(id, data)
    return {"ok": True}

@router.delete("/channels/{id}")
def delete_channel(id: int):
    delete_channel_service(id)
    return {"ok": True}


# TRACKING LINKS ----------------

@router.post("/tracking-links")
def create_tracking_link(data: TrackingLink):
    insert_tracking_link(data)
    return {"ok": True}

@router.get("/tracking-links")
def get_tracking_links():
    return read_table("tracking_links")

@router.put("/tracking-links/{id}")
def update_tracking_link(id: int, data: TrackingLink):
    update_tracking_link_service(id, data)
    return {"ok": True}

@router.delete("/tracking-links/{id}")
def delete_tracking_link(id: int):
    delete_tracking_link_service(id)
    return {"ok": True}


# CLICKS ----------------

@router.post("/clicks")
def create_click(data: Click):
    insert_click(data)
    return {"ok": True}

@router.get("/clicks")
def get_clicks():
    return read_table("clicks")

@router.put("/clicks/{id}")
def update_click(id: int, data: Click):
    update_click_service(id, data)
    return {"ok": True}

@router.delete("/clicks/{id}")
def delete_click(id: int):
    delete_click_service(id)
    return {"ok": True}


# CONVERSIONS ----------------

@router.post("/conversions")
def create_conversion(data: Conversion):
    insert_conversion(data)
    return {"ok": True}

@router.get("/conversions")
def get_conversions():
    return read_table("conversions")

@router.put("/conversions/{id}")
def update_conversion(id: int, data: Conversion):
    update_conversion_service(id, data)
    return {"ok": True}

@router.delete("/conversions/{id}")
def delete_conversion(id: int):
    delete_conversion_service(id)
    return {"ok": True}

@router.get("/campaigns/top")
def get_top_campaigns(limit: int = 5):
    from app.db.database import run_query
    resultado = run_query("""
        SELECT c.id_campaign, c.name, 
               COALESCE(SUM(cv.revenue), 0) as ingresos,
               c.spent,
               COALESCE(SUM(cv.revenue), 0) - c.spent as beneficio
        FROM campaigns c
        LEFT JOIN conversions cv ON c.id_campaign = cv.id_campaign
        GROUP BY c.id_campaign
        ORDER BY beneficio DESC
        LIMIT %s
    """, (limit,), fetch=True)
    return resultado
