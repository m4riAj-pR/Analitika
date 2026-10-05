from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import run_query
from app.security import require_role

# Todos los endpoints bajo este router exigen estrictamente rol Super Admin (1)
router = APIRouter(dependencies=[Depends(require_role([1]))])


@router.get("/companies")
def get_admin_companies():
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
def get_users_by_role(id_company: int = None):
    """Retorna usuarios agrupados por rol, opcionalmente filtrados por empresa."""
    where_clause = ""
    params = []
    if id_company:
        where_clause = " AND uc.id_company = %s"
        params = [id_company]

    owners_query = f"""
        SELECT u.id_user, p.email, u.id_role, r.name as role_name 
        FROM users u 
        JOIN persons p ON u.id_person = p.id_person 
        JOIN roles r ON u.id_role = r.id_role
        JOIN user_company uc ON u.id_user = uc.id_user
        WHERE u.id_role = 2{where_clause}
    """

    managers_query = f"""
        SELECT u.id_user, p.email, u.id_role, r.name as role_name 
        FROM users u 
        JOIN persons p ON u.id_person = p.id_person 
        JOIN roles r ON u.id_role = r.id_role
        JOIN user_company uc ON u.id_user = uc.id_user
        WHERE u.id_role = 3{where_clause}
    """

    owners = run_query(owners_query, params, fetch=True)
    managers = run_query(managers_query, params, fetch=True)

    return {
        "owners": owners,
        "managements": managers
    }


@router.put("/users/{id_user}/role")
def update_user_role(id_user: int, payload: dict):
    """Actualiza el rol de un usuario."""
    new_role = payload.get("id_role")
    if new_role not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Rol inválido")

    run_query("UPDATE users SET id_role = %s WHERE id_user = %s", (new_role, id_user))
    return {"message": "Rol actualizado correctamente"}
