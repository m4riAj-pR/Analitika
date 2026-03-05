from pydantic import BaseModel

class Usuario(BaseModel):
    id_usuario: int 
    email: str
    nombre: str
    apellidos: str
    rol: str
    password_hash:str