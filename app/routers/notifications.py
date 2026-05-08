from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.database import run_query
from app.security import get_current_user
from app.schemas.notifications import NotificationPublic

router = APIRouter()

@router.get("/", response_model=List[NotificationPublic])
def get_notifications(current_user: dict = Depends(get_current_user)):
    results = run_query("""
        SELECT * FROM notifications 
        WHERE id_user = %s 
        ORDER BY created_at DESC
    """, (current_user["id_user"],), fetch=True)
    return results

@router.put("/{id_notification}/read")
def mark_as_read(id_notification: int, current_user: dict = Depends(get_current_user)):
    # Verificar propiedad
    notif = run_query("SELECT id_user FROM notifications WHERE id_notification = %s", (id_notification,), fetch=True)
    if not notif or notif[0]["id_user"] != current_user["id_user"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta notificación")
    
    run_query("UPDATE notifications SET is_read = 1 WHERE id_notification = %s", (id_notification,))
    return {"ok": True}

@router.get("/unread-count")
def get_unread_count(current_user: dict = Depends(get_current_user)):
    result = run_query("""
        SELECT COUNT(*) as count FROM notifications 
        WHERE id_user = %s AND is_read = 0
    """, (current_user["id_user"],), fetch=True)
    return {"count": result[0]["count"] if result else 0}
