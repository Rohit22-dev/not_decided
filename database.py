import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL = "postgresql://postgres:rk220101@localhost:5432/not_decided"
DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")


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
        try:
            if hasattr(self, "cursor") and self.cursor:
                self.cursor.close()
            if hasattr(self, "connection") and self.connection:
                self.connection.close()
        except psycopg2.Error as e:
            print(f"Error closing database connection: {e}")


@contextmanager
def get_db():
    """Provide a database connection to FastAPI routes."""
    db_conn = DatabaseConnection()
    try:
        yield db_conn
    finally:
        db_conn.close()
