from pydantic import BaseModel

class Lectura(BaseModel):
    id: int
    fechahora: str
    valor: float
    sensor_id: int