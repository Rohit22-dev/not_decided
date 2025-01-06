from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime
from event.constants import EventStatus


class EventCreate(BaseModel):
    name: constr(min_length=1, max_length=255)
    description: Optional[str]
    location: constr(min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    status: str = EventStatus.UPCOMING

    def validate_status(self):
        if self.status not in EventStatus.values():
            raise ValueError(f"Invalid status. Must be one of: {', '.join(EventStatus.values())}")


class EventUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    location: Optional[constr(min_length=1, max_length=255)]
    start_time: Optional[str]
    end_time: Optional[str]
    event_date: str
    status: Optional[str]

    def validate_status(self):
        if self.status and self.status not in EventStatus.values():
            raise ValueError(f"Invalid status. Must be one of: {', '.join(EventStatus.values())}")


class EventResponse(EventCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
