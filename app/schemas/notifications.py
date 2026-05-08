from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str
    is_read: Optional[bool] = False

class NotificationCreate(NotificationBase):
    id_user: int

class NotificationPublic(NotificationBase):
    id_notification: int
    id_user: int
    created_at: datetime

    class Config:
        from_attributes = True
