from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------------------------------------------
# DATABASE URL
# ------------------------------------------------------------------
# SQLite stores data in a local file.
#
# sqlite:///./app.db means:
#
# sqlite:///
#     SQLite database
#
# ./app.db
#     Create a file named app.db in the current directory

# moved to postgresql
# Database_URL = "sqlite:///./test.db"
Database_URL = "postgresql://postgres:muzamil@localhost:5432/mas_ai"

# ------------------------------------------------------------------
# CREATE DATABASE ENGINE
# ------------------------------------------------------------------
# The engine is SQLAlchemy's connection manager.
#
# Think of it as:
# FastAPI ---> Engine ---> Database
#
# Every database operation eventually goes through this engine.
# It handles the connection pooling, SQL execution, and more.

engine = create_engine(
    Database_URL, 
    # SQLite has a restriction where the same thread
    # should use the same connection.
    #
    # FastAPI may use multiple threads internally.
    #
    # This option prevents thread-related errors.
    pool_pre_ping=True,  # Automatically check if connections are alive
    # not needed in postgresql
    # connect_args={"check_same_thread": False}  # Required for SQLite to allow multiple threads
)

# ------------------------------------------------------------------
# CREATE SESSION FACTORY
# ------------------------------------------------------------------
# SessionLocal is NOT a database session.
#
# It is a factory that creates sessions.
#
# Every API request will get its own session.
# This ensures that database operations are isolated per request.

SessionLocal = sessionmaker(autocommit = False,
                            autoflush=False,
                            bind=engine)

# ------------------------------------------------------------------
# BASE CLASS FOR MODELS
# ------------------------------------------------------------------
# Every SQLAlchemy model will inherit from Base.
# This allows SQLAlchemy to keep track of all models and create tables accordingly.

Base = declarative_base()

# ------------------------------------------------------------------
# DATABASE DEPENDENCY
# ------------------------------------------------------------------
# This function provides a database session
# to FastAPI endpoints.
#
# FastAPI automatically:
#
# 1. Calls this function
# 2. Creates session
# 3. Gives session to route
# 4. Closes session after request

def get_db():

    # Create a new db session
    db = SessionLocal()
    try:
         # Yield returns the session
        # to the API endpoint.
        yield db
    finally:
        # Always close the session.
        #
        # This is important because open
        # connections consume resources.
        #
        db.close()