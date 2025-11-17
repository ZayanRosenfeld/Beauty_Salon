from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, database
from .client_schemas import Client, ClientSummary

router = APIRouter()

# Dependence of database
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Add client
@router.post("/clients", response_model=Client)
def create_client(client: Client, db: Session = Depends(get_db)):
    db_client = models.Client(
        id=client.id,
        name=client.name,
        phone=client.phone,
        appointments=client.appointments,
        timestamp=client.timestamp,
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


# List all clients, relatively
@router.get("/clients", response_model=List[ClientSummary])
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    return clients

# Obter cliente por ID
@router.get("/clients/{client_id}", response_model=Client)
def get_client_details(client_id: int, db: Session = Depends(get_db)):
    """
    Busca um cliente específico pelo ID.
    """
    client = db.query(models.Client).filter(models.Client.id == client_id).first()

    if client is None:
        # Retorna 404 Not Found se o cliente não for encontrado
        raise HTTPException(status_code=404, detail=f"Cliente com ID {client_id} não encontrado")

    return client