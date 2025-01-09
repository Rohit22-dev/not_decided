from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from common.auth_utils import verify_token
from common.database import get_mongo_db, get_postgresql_db
from common.helpers import db_connection_handler

from . import models

event = APIRouter(dependencies=[Depends(verify_token)])


@event.post("/", response_model=models.EventResponse)
@db_connection_handler
async def create_event(
    event: models.EventCreate,
    user: dict = Depends(verify_token),
    db_conn=Depends(get_postgresql_db),
):
    """Create a new event."""
    organizer_id = user.get("user_id")

    query = sql.SQL(
        """INSERT INTO events (event_name, description, location, start_time, end_time, event_date, organizer_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) 
                       RETURNING event_id, event_name, description, location, start_time, end_time, event_date, organizer_id,created_at,updated_at;"""
    )
    db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)

    db_conn.cursor.execute(
        query,
        (
            event.event_name,
            event.description,
            event.location,
            event.start_time,
            event.end_time,
            event.event_date,
            organizer_id,
        ),
    )
    event_data = db_conn.cursor.fetchone()
    db_conn.connection.commit()
    return models.EventResponse(**event_data)


@event.get("/", response_model=list[models.EventResponse])
@db_connection_handler
async def read_events(
    skip: int = 0, limit: int = 10, db_conn=Depends(get_postgresql_db)
):
    """Get all events."""
    query = sql.SQL(
        """SELECT event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at
                       FROM events
                       LIMIT %s OFFSET %s;"""
    )

    db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)

    # Execute the query with pagination
    db_conn.cursor.execute(query, (limit, skip))
    events = db_conn.cursor.fetchall()

    return [models.EventResponse(**event) for event in events]


@event.get("/{event_id}", response_model=models.EventResponse)
@db_connection_handler
async def read_event(event_id: str, db_conn=Depends(get_postgresql_db)):
    query = sql.SQL(
        """SELECT event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at
                       FROM events WHERE event_id = %s;"""
    )

    db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    db_conn.cursor.execute(query, (event_id,))

    event = db_conn.cursor.fetchone()
    # If no event is found, raise a 404 HTTPException
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return models.EventResponse(**event)


@event.put("/{event_id}", response_model=models.EventResponse)
@db_connection_handler
async def update_event(
    event_id: str, event: models.EventUpdate, db_conn=Depends(get_postgresql_db)
):
    """Update a specific event."""

    query = sql.SQL(
        """UPDATE events
                       SET event_name = %s, description = %s, location = %s, start_time = %s, end_time = %s, event_date = %s
                       WHERE event_id = %s
                       RETURNING event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at;"""
    )

    db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    db_conn.cursor.execute(
        query,
        (
            event.event_name,
            event.description,
            event.location,
            event.start_time,
            event.end_time,
            event.event_date,
            event_id,
        ),
    )

    updated_event = db_conn.cursor.fetchone()

    # If no event was updated, raise a 404 HTTPException
    if updated_event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return models.EventResponse(**updated_event)


@event.delete("/{event_id}")
@db_connection_handler
async def delete_event(event_id: str, db_conn=Depends(get_postgresql_db)):
    """Delete a specific event."""
    # TODO: Delete is not working
    query = sql.SQL("""DELETE FROM events WHERE event_id = %s RETURNING event_id;""")

    db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    db_conn.cursor.execute(query, (event_id,))
    deleted_event = db_conn.cursor.fetchone()

    # If no event was deleted, raise a 404 HTTPException
    if deleted_event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return {"message": "Event deleted successfully"}


@event.post("/{event_id}/reviews", response_model=models.ReviewResponse)
@db_connection_handler
async def create_review(
    event_id: str,
    review: models.ReviewCreate,
    user: dict = Depends(verify_token),
    db=Depends(get_mongo_db),
):
    """Add a review for a specific event."""
    user_id = user.get("user_id")
    review_data = {
        "event_id": event_id,
        "user_id": user_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
    }
    result = db.reviews.insert_one(review_data)
    review_data["_id"] = str(result.inserted_id)
    return review_data


@event.get("/{event_id}/reviews", response_model=List[models.ReviewResponse])
@db_connection_handler
async def get_reviews_by_event(event_id: str, db=Depends(get_mongo_db)):
    """Get all reviews for a specific event."""
    reviews = list(db.reviews.find({"event_id": event_id}))
    for review in reviews:
        review["_id"] = str(review["_id"])
    return reviews


@event.delete("/reviews/{review_id}")
@db_connection_handler
async def delete_review(review_id: str, db=Depends(get_mongo_db)):
    """Delete a specific review."""
    result = db.reviews.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted successfully"}
