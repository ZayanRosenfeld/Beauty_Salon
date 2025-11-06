from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

app = FastAPI()


# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# /// Configuration ///
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'salon.db')}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# /// Models ///
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_visits = Column(Integer, default=0)

    appointments = relationship("Appointment", back_populates="client", cascade="all, delete-orphan")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="appointments")


# /// Create tables (safe to run multiple times, it will let you know if you data already exists) ///
Base.metadata.create_all(bind=engine)

# /// Pydantic Schemas ///
class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = None

class ClientOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    created_at: datetime
    total_visits: int

    class Config:
        orm_mode = True

class AppointmentCreate(BaseModel):
    # front-end could send client_id though its optional
    client_id: Optional[int] = None
    name: Optional[str] = None
    service: str

class AppointmentOut(BaseModel):
    id: int
    client_id: int
    service: str
    created_at: datetime

    class Config:
        orm_mode = True


# /// FastAPI app (backbone) ///
app = FastAPI(title="Salon Bridge API (SQLite)")

# Allow CORS from anywhere for development, needed for network compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /// Database dependency //
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# /// Routes necessary for code to navigate here ///
@app.get("/clients", response_model=List[ClientOut])
def list_clients():
    db = SessionLocal()
    clients = db.query(Client).order_by(Client.name).all()
    db.close()
    return clients


@app.post("/clients", response_model=ClientOut)
def create_client(payload: ClientCreate):
    db = SessionLocal()
    # Optionally avoid duplicate names
    client = Client(name=payload.name, phone=payload.phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    db.close()
    return client


@app.get("/appointments", response_model=List[AppointmentOut])
def list_appointments():
    db = SessionLocal()
    appts = db.query(Appointment).order_by(Appointment.created_at.desc()).all()
    db.close()
    return appts


@app.post("/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate):
    db = SessionLocal()

    # 1) If client_id is provided - find it
    client = None
    if payload.client_id is not None:
        client = db.query(Client).filter(Client.id == payload.client_id).first()
        if not client:
            db.close()
            raise HTTPException(status_code=404, detail="Client id not found.")

    # 2) If client_id missing, yet name provided - find by name or create
    if client is None:
        if payload.name:
            client = db.query(Client).filter(Client.name == payload.name).first()
            if not client:
                # create new client with given name (phone unknown)
                client = Client(name=payload.name)
                db.add(client)
                db.commit()
                db.refresh(client)
        else:
            db.close()
            raise HTTPException(status_code=400, detail="Either client_id or name must be provided.")

    # 3) Create appointment linked to client
    new_appt = Appointment(client_id=client.id, service=payload.service)
    db.add(new_appt)

    # 4) Update client stats: increment total_visits
    client.total_visits = (client.total_visits or 0) + 1

    db.commit()
    db.refresh(new_appt)
    db.refresh(client)
    db.close()
    return new_appt


# Get history for a client
@app.get("/clients/{client_id}/history", response_model=List[AppointmentOut])
def client_history(client_id: int):
    db = SessionLocal()
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        db.close()
        raise HTTPException(status_code=404, detail="Client not found.")
    appts = db.query(Appointment).filter(Appointment.client_id == client_id).order_by(Appointment.created_at.desc()).all()
    db.close()
    return appts
