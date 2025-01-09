from datetime import datetime

from pydantic import BaseModel, condecimal


class TicketCreate(BaseModel):
    user_id: int
    ticket_type: str  # Example: "General", "VIP", "Early Bird", "Group", "Virtual"
    price: condecimal(max_digits=10, decimal_places=2)


class TicketResponse(TicketCreate):

    class Config:
        from_attributes = True

    ticket_id: int
    event_id: int
    purchased_at: datetime
