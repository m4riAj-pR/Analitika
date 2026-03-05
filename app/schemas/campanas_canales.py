from pydantic import BaseModel

class CampanaCanal(BaseModel):
    campana_id: int
    canal_id: int