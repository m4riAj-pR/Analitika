from pydantic import BaseModel
class Dispositivo(BaseModel):
    id: int
    referencia: str
    descripcion: str
    dispositivo_id: int