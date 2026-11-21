from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .models import Privilege


class User(BaseModel):
    id: int
    name: str
    email: str
    password: str
    is_active: bool = True
    privilage: Privilege = Privilege.user
    date_created: datetime
    date_modified: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    privilage: Privilege | None = None
