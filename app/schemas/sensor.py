from pydantic import BaseModel

class Sensor(BaseModel):
    id: int
    referencia: str
    descripcion: str
    dispositivo_id: int