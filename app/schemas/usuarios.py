from pydantic import BaseModel

class Usuario(BaseModel):
    id_usuario: int 
    email: str
    nombres: str
    apellidos: str
    rol: str
    password_hash:str