from typing import List

from fastapi import APIRouter, Depends, HTTPException

from common.auth_utils import verify_token
from common.database import get_postgresql_db

from .models import TicketCreate, TicketResponse

ticket = APIRouter(dependencies=[Depends(verify_token)])


@ticket.post("/events/{event_id}/tickets", response_model=TicketResponse)
def create_ticket(event_id: int, ticket: TicketCreate, db=Depends(get_postgresql_db)):
    query = """
        INSERT INTO tickets (event_id, user_id, ticket_type, price)
        VALUES (%s, %s, %s, %s)
        RETURNING ticket_id, event_id, user_id, ticket_type, price, purchased_at;
    """
    try:
        db.cursor.execute(
            query,
            (event_id, ticket.user_id, ticket.ticket_type, ticket.price),
        )
        ticket_data = db.cursor.fetchone()
        db.connection.commit()
        return ticket_data
    except Exception as e:
        db.connection.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {e}")


@ticket.get("/users/{user_id}/tickets", response_model=List[TicketResponse])
def get_tickets_by_user(user_id: int, db=Depends(get_postgresql_db)):
    query = """
        SELECT ticket_id, event_id, user_id, ticket_type, price, purchased_at
        FROM tickets WHERE user_id = %s;
    """
    try:
        db.cursor.execute(query, (user_id,))
        tickets = db.cursor.fetchall()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {e}")


@ticket.get("/events/{event_id}/tickets", response_model=List[TicketResponse])
def get_tickets_by_event(event_id: int, db=Depends(get_postgresql_db)):
    query = """
        SELECT ticket_id, event_id, user_id, ticket_type, price, purchased_at
        FROM tickets WHERE event_id = %s;
    """
    try:
        db.cursor.execute(query, (event_id,))
        tickets = db.cursor.fetchall()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {e}")


@ticket.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: int, db=Depends(get_postgresql_db)):
    query = "DELETE FROM tickets WHERE ticket_id = %s RETURNING ticket_id;"
    try:
        db.cursor.execute(query, (ticket_id,))
        deleted_ticket = db.cursor.fetchone()
        if not deleted_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        db.connection.commit()
        return {
            "message": "Ticket deleted successfully",
            "ticket_id": deleted_ticket[0],
        }
    except Exception as e:
        db.connection.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete ticket: {e}")
