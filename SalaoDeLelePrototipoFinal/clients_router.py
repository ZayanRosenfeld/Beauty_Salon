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
