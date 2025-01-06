from sqlalchemy.orm import Session
from .schemas import Event
from .models import EventCreate, EventUpdate


def create_event(db: Session, event: EventCreate):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_events(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Event).offset(skip).limit(limit).all()


def get_event_by_id(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()


def update_event(db: Session, event_id: int, event: EventUpdate):
    db_event = get_event_by_id(db, event_id)
    if db_event:
        for key, value in event.dict(exclude_unset=True).items():
            setattr(db_event, key, value)
        db.commit()
        db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int):
    db_event = get_event_by_id(db, event_id)
    if db_event:
        db.delete(db_event)
        db.commit()
    return db_event
