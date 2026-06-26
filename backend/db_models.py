from sqlalchemy import Column, Integer, String
from backend.database import Base

# ------------------------------------------------------------------
# USER TABLE
# ------------------------------------------------------------------
# This class represents a table in the database.
#
# SQLAlchemy converts this Python class into SQL.

class User(Base):
    # Table name in the database

    __tablename__ = "users"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True
    )

    email = Column(
        String,
        unique=True,
    )

    password = Column(
        String,
    )

    role = Column(
        String,
        default="candidate"
    )