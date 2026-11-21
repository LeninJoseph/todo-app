from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, TIMESTAMP, text
from sqlalchemy.orm import relationship
import enum
from .db import Base


class Privilege(enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    email = Column(String(255), index=True, unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    privilage = Column(Enum(Privilege), default=Privilege.user, nullable=False)
    date_created = Column(TIMESTAMP(timezone=True),
                          nullable=False, server_default=text('now()'))
    date_modified = Column(TIMESTAMP(timezone=True), nullable=False,
                           server_default=text('now()'), onupdate=text('now()'))
