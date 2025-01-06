from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth_utils import verify_token
from database import get_db

from . import crud, models
from .models import EventCreate, EventUpdate

event = APIRouter(dependencies=[Depends(verify_token)])


@event.post("/", response_model=models.EventResponse)
def create_(
    event: EventCreate,
    db: Session = Depends(get_db),
):
    return crud.create_event(db, event)


@event.get("/", response_model=list[models.EventResponse])
def read_events(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_events(db, skip=skip, limit=limit)


@event.get("/{event_id}", response_model=models.EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@event.put("/{event_id}", response_model=models.EventResponse)
def update_event(event_id: int, event: EventUpdate, db: Session = Depends(get_db)):
    updated_event = crud.update_event(db, event_id, event)
    if updated_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated_event


@event.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.delete_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}
