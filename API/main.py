from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import SQLModel, Field, create_engine, Session, select
import uuid
import datetime

# Database setup
DATABASE_URL = "sqlite:///./events.db"
engine = create_engine(DATABASE_URL)

# Event model
class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    event_code: str = Field(index=True)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)

# Create the database tables
SQLModel.metadata.create_all(bind=engine)

# FastAPI setup
app = FastAPI(redoc_url="/")
security = HTTPBasic()

# Dummy credentials (in production, store securely)
USERNAME = "username"
PASSWORD = "password"

# Dependency for password protection
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

# Request model for adding events
class EventCreate(SQLModel):
    event_code: str

@app.post("/add_event", dependencies=[Depends(verify_credentials)])
def create_event(event: EventCreate, db: Session = Depends(lambda: Session(engine))):
    new_event = Event(event_code=event.event_code)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return {
        "id": new_event.id,
        "event_code": new_event.event_code,
        "timestamp": new_event.timestamp,
        "uuid": new_event.uuid,
    }

@app.get("/events", dependencies=[Depends(verify_credentials)])
def read_events(db: Session = Depends(lambda: Session(engine))):
    events = db.exec(select(Event)).all()
    return [
        {
            "id": event.id,
            "event_code": event.event_code,
            "timestamp": event.timestamp,
            "uuid": event.uuid,
        }
        for event in events
    ]

# Close the session after request
@app.middleware("http")
async def db_session_middleware(request, call_next):
    response = await call_next(request)
    db_session = Session(engine)
    db_session.close()
    return response
