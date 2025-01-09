import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import psycopg2
import redis
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session

from auth.models import Token, UserCreate, UserResponse
from common.auth_utils import verify_token
from common.database import DatabaseConnection, RedisConnection

load_dotenv()
auth = APIRouter()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_PORT = os.getenv("REDIS_PORT")

# Move these to environment variables in production
SECRET_KEY = "1e9356e2ef00d712c017be0e7f5e8ae5da1fa4f60522cc35638148566f0932f9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Token creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token",
        )


def get_user_from_db(email: str, db: Session) -> Optional[UserResponse]:
    try:
        db_conn = DatabaseConnection()
        query = sql.SQL(
            """
            SELECT u.user_id, u.username, u.email, r.role_name 
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.email = %s
        """
        )
        db_conn.cursor.execute(query, (email,))
        user = db_conn.cursor.fetchone()

        if user:
            return UserResponse(id=user[0], name=user[1], email=user[2], role=user[3])
        return None
    except psycopg2.Error as e:
        print(f"Database query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )


@auth.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    try:
        user.validate_role()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    existing_user = get_user_from_db(user.email, "users")
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    db_conn = DatabaseConnection()
    try:
        # Get the role_id corresponding to the role_name
        query = sql.SQL("SELECT role_id FROM roles WHERE role_name = %s")
        db_conn.cursor.execute(query, (user.role,))
        role = db_conn.cursor.fetchone()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role"
            )

        role_id = role[0]
        hashed_password = get_password_hash(user.password)

        query = sql.SQL(
            """
            INSERT INTO users (username, email, role_id, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, username, email, role_id
        """
        )
        db_conn.cursor.execute(query, (user.name, user.email, role_id, hashed_password))
        new_user_data = db_conn.cursor.fetchone()
        db_conn.connection.commit()

        return UserResponse(
            id=new_user_data[0],
            name=new_user_data[1],
            email=new_user_data[2],
            role=user.role,
        )
    except psycopg2.Error as e:
        db_conn.connection.rollback()
        print(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )
    # finally:
    #     db_conn.close()


@auth.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        db_conn = DatabaseConnection()
        redis_client = RedisConnection().connection
        query = sql.SQL("SELECT user_id, password_hash FROM users WHERE email = %s")
        db_conn.cursor = db_conn.connection.cursor(cursor_factory=RealDictCursor)
        db_conn.cursor.execute(query, (form_data.username,))
        user_data = db_conn.cursor.fetchone()

        if not user_data or not verify_password(
            form_data.password, user_data.get("password_hash")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(
            data={"email": form_data.username, "user_id": user_data.get("user_id")},
        )

        # Store token in Redis with error handling
        try:
            redis_client.set(
                form_data.username, access_token, ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except redis.RedisError as e:
            print(f"Redis operation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session management error",
            )

        return {"access_token": access_token, "token_type": "bearer"}
    except psycopg2.Error as e:
        print(f"Database query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
    # finally:
    #     db_conn.close()


@auth.post("/logout")
async def logout_user(token_payload: str = Depends(verify_token)):
    try:
        redis_client = RedisConnection().connection
        email = token_payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        try:
            redis_client.delete(email)
        except redis.RedisError as e:
            print(f"Redis operation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session management error",
            )

        return {"detail": "Logout successful"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@auth.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        redis_client = RedisConnection().connection
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        try:
            token_in_redis = redis_client.get(email)
            if not token_in_redis or token_in_redis != token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
                )
        except redis.RedisError as e:
            print(f"Redis operation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session management error",
            )

        user = get_user_from_db(email, None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
