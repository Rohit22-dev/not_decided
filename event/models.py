from datetime import datetime, time, timezone
from typing import Optional

from pydantic import BaseModel, conint, constr

from event.constants import EventStatus


class EventCreate(BaseModel):
    event_name: constr(min_length=1, max_length=255)
    description: Optional[str]
    location: constr(min_length=1, max_length=255)
    start_time: time
    end_time: time
    event_date: datetime
    status: str = EventStatus.UPCOMING

    def validate_status(self):
        if self.status not in EventStatus.values():
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(EventStatus.values())}"
            )


class EventUpdate(BaseModel):
    event_name: Optional[constr(min_length=1, max_length=255)]
    description: Optional[str]
    location: Optional[constr(min_length=1, max_length=255)]
    start_time: time
    end_time: time
    event_date: datetime
    status: Optional[str]

    def validate_status(self):
        if self.status and self.status not in EventStatus.values():
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(EventStatus.values())}"
            )


class EventResponse(EventCreate):
    class Config:
        from_attributes = True

    event_id: str
    created_at: datetime
    updated_at: datetime


class ReviewCreate(BaseModel):
    rating: conint(ge=1, le=5)  # Rating between 1 and 5
    comment: constr(max_length=500)
    created_at: datetime = datetime.now(timezone.utc)


class ReviewResponse(ReviewCreate):
    event_id: str
    user_id: str
