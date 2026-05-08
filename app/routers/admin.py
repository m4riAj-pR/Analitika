from fastapi import APIRouter, Depends, HTTPException
from app.db.database import run_query
from app.security import get_current_user

router = APIRouter()

def get_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["id_role"] != 1:
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere rol Super Admin")
    return current_user

@router.get("/companies")
def get_admin_companies(current_user: dict = Depends(get_super_admin)):
    """Retorna lista de empresas con conteo de owners y managers."""
    return run_query("""
        SELECT 
            c.id_company, 
            c.name as nombre_empresa,
            (SELECT COUNT(*) FROM user_company uc 
             JOIN users u ON uc.id_user = u.id_user 
             WHERE uc.id_company = c.id_company AND u.id_role = 2) as owners,
            (SELECT COUNT(*) FROM user_company uc 
             JOIN users u ON uc.id_user = u.id_user 
             WHERE uc.id_company = c.id_company AND u.id_role = 3) as managements
        FROM companies c
        ORDER BY c.name ASC
    """, fetch=True)

@router.get("/users-by-role")
def get_users_by_role(current_user: dict = Depends(get_super_admin)):
    """Retorna usuarios agrupados por rol para la vista de Roles."""
    owners = run_query("""
        SELECT u.id_user, p.email, r.name as role_name 
        FROM users u 
        JOIN persons p ON u.id_person = p.id_person 
        JOIN roles r ON u.id_role = r.id_role
        WHERE u.id_role = 2
    """, fetch=True)
    
    managers = run_query("""
        SELECT u.id_user, p.email, r.name as role_name 
        FROM users u 
        JOIN persons p ON u.id_person = p.id_person 
        JOIN roles r ON u.id_role = r.id_role
        WHERE u.id_role = 3
    """, fetch=True)
    
    return {
        "owners": owners,
        "managements": managers
    }
