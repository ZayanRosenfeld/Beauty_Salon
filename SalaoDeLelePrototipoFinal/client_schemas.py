from pydantic import BaseModel

# Schema completo (para criar/atualizar)
class Client(BaseModel):
    id: int
    name: str
    phone: str
    appointments: int
    timestamp: str  # ou datetime, se preferir

    class Config:
        orm_mode = True

# Schema resumido (para listar apenas o essencial)
class ClientSummary(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
