from functools import wraps

import psycopg2
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError


def db_connection_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except (psycopg2.Error, PyMongoError) as e:
            db_type = "PostgreSQL" if isinstance(e, psycopg2.Error) else "MongoDB"
            print(f"{db_type} error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{db_type} operation failed: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unexpected error: {e}",
            )

    return wrapper
