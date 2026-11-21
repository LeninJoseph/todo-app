from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from security import hash_password, require_admin
from db import schemas
from db.crud import CRUDBase
from db.db import get_db
from db.models import User

router = APIRouter(prefix="/users", tags=["users"])


class CRUDUser(CRUDBase[User]):
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))


user_crud = CRUDUser(User)

# Never return the password hash to clients.
HIDE = {"password"}


@router.post("/", response_model=schemas.User, response_model_exclude=HIDE,
             status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    try:
        data = payload.model_dump()
        data["password"] = hash_password(data["password"])
        return user_crud.create(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")


@router.get("/", response_model=list[schemas.User], response_model_exclude=HIDE)
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               _: User = Depends(require_admin)):
    return user_crud.get_multi(db, skip, limit)


@router.get("/{user_id}", response_model=schemas.User, response_model_exclude=HIDE)
def read_user(user_id: int, db: Session = Depends(get_db),
              _: User = Depends(require_admin)):
    user = user_crud.get(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.patch("/{user_id}", response_model=schemas.User, response_model_exclude=HIDE)
def update_user(user_id: int, payload: schemas.UserUpdate,
                db: Session = Depends(get_db), _: User = Depends(require_admin)):
    fields = payload.model_dump(exclude_unset=True)
    if "password" in fields:
        fields["password"] = hash_password(fields["password"])
    try:
        user = user_crud.update(db, user_id, fields)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    if not user_crud.delete(db, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
