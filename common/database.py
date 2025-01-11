import os

import psycopg2
import redis
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# NOTE: For local setup
# DATABASE_URL = "postgresql://postgres:rk220101@localhost:5432/not_decided"
# REDIS_HOST = "localhost"
# REDIS_PORT = "6379"
# MONGODB_URL = "mongodb://localhost:27017/not_decided"


DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
MONGODB_URL = os.getenv("MONGODB_URL")


class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            try:
                cls._instance.connection = psycopg2.connect(
                    DATABASE_URL, connect_timeout=5
                )
                cls._instance.connection.autocommit = False
                cls._instance.cursor = cls._instance.connection.cursor()
                print("Database connection established")
            except psycopg2.Error as e:
                print(f"Database connection failed: {e}")
                raise
        return cls._instance

    def close(self):
        """Close the database connection and cursor."""
        try:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection closed")
        except psycopg2.Error as e:
            print(f"Error closing database connection: {e}")


def get_postgresql_db():
    """Provide a database connection to FastAPI routes."""
    db_conn = DatabaseConnection()
    try:
        yield db_conn
    finally:
        db_conn.close()


class RedisConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisConnection, cls).__new__(cls)
            try:
                cls._instance.connection = redis.StrictRedis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                # Test connection
                cls._instance.connection.ping()
                print("Connected to Redis Labs successfully!")
            except redis.ConnectionError as e:
                print(f"Failed to connect to Redis: {e}")
                raise
        return cls._instance

    def close(self):
        try:
            if hasattr(self, "connection") and self.connection:
                self.connection.close()
            print("Redis connection closed")
        except redis.ConnectionError as e:
            print(f"Error closing Redis connection: {e}")


def get_redis_connection():
    """Provide a Redis connection."""
    redis_conn = RedisConnection()
    try:
        yield redis_conn.connection
    finally:
        redis_conn.close()


class MongoDBConnection:
    _instance = None

    def __new__(cls):
        # Use the singleton pattern to ensure only one instance
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                # Establish MongoDB connection using MongoClient
                cls._instance.client = MongoClient(MONGODB_URL)
                database_name = os.getenv("MONGODB_DATABASE", "default_db")
                cls._instance.db = cls._instance.client[
                    database_name
                ]  # Default database from the URL
                print("MongoDB connection established")
            except Exception as e:
                print(f"MongoDB connection failed: {e}")
                raise
        return cls._instance

    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            print("MongoDB connection closed")
        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")


def get_mongo_db():
    """Provide a MongoDB connection."""
    mongo_conn = MongoDBConnection()
    try:
        yield mongo_conn.db  # Yield the database instance
    finally:
        mongo_conn.close()
