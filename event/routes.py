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


def execute_query(cursor, query, params=None):
    """Helper function to execute a query and fetch results."""
    cursor.execute(query, params or ())
    return cursor.fetchone()


def execute_query_fetchall(cursor, query, params=None):
    """Helper function to execute a query and fetch all results."""
    cursor.execute(query, params or ())
    return cursor.fetchall()


@event.post("/", response_model=models.EventResponse)
@db_connection_handler
async def create_event(
    event: models.EventCreate,
    user: dict = Depends(verify_token),
    db_conn=Depends(get_postgresql_db),
):
    """Create a new event."""
    query = sql.SQL(
        """
        INSERT INTO events (event_name, description, location, start_time, end_time, event_date, organizer_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s) 
        RETURNING event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at;
        """
    )
    organizer_id = user.get("user_id")
    cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    event_data = execute_query(
        cursor,
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
    db_conn.connection.commit()
    return models.EventResponse(**event_data)


@event.get("/", response_model=List[models.EventResponse])
@db_connection_handler
async def read_events(
    skip: int = 0, limit: int = 10, db_conn=Depends(get_postgresql_db)
):
    """Get all events with pagination."""
    query = sql.SQL(
        """
        SELECT event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at
        FROM events
        LIMIT %s OFFSET %s;
        """
    )
    cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    events = execute_query_fetchall(cursor, query, (limit, skip))
    return [models.EventResponse(**event) for event in events]


@event.get("/{event_id}", response_model=models.EventResponse)
@db_connection_handler
async def read_event(event_id: str, db_conn=Depends(get_postgresql_db)):
    """Get details of a specific event."""
    query = sql.SQL(
        """
        SELECT event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at
        FROM events
        WHERE event_id = %s;
        """
    )
    cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    event = execute_query(cursor, query, (event_id,))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return models.EventResponse(**event)


@event.put("/{event_id}", response_model=models.EventResponse)
@db_connection_handler
async def update_event(
    event_id: str, event: models.EventUpdate, db_conn=Depends(get_postgresql_db)
):
    """Update a specific event."""
    query = sql.SQL(
        """
        UPDATE events
        SET event_name = %s, description = %s, location = %s, start_time = %s, end_time = %s, event_date = %s
        WHERE event_id = %s
        RETURNING event_id, event_name, description, location, start_time, end_time, event_date, organizer_id, created_at, updated_at;
        """
    )
    cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    updated_event = execute_query(
        cursor,
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
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return models.EventResponse(**updated_event)


@event.delete("/{event_id}")
@db_connection_handler
async def delete_event(event_id: str, db_conn=Depends(get_postgresql_db)):
    """Delete a specific event."""
    query = sql.SQL("DELETE FROM events WHERE event_id = %s RETURNING event_id;")
    cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
    deleted_event = execute_query(cursor, query, (event_id,))
    if not deleted_event:
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
    review_data = {
        "event_id": event_id,
        "user_id": user.get("user_id"),
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
