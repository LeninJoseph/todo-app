import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings, redis
from db.db import get_db
from db.models import Privilege, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---- passwords ----
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"{salt.hex()}${digest.hex()}"  # 97 chars, fits String(100)


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
    except ValueError:
        return False
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(digest, expected)


# ---- tokens ----
def _token_key(token: str) -> str:
    # Store a hash, not the raw token, so a Redis leak doesn't leak usable tokens.
    return "token:" + hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: int) -> str:
    ttl = timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + ttl}
    token = jwt.encode(payload, settings.secret_key,
                       algorithm=settings.algorithm)
    redis.set(_token_key(token), user_id, ex=int(ttl.total_seconds()))
    return token


def revoke_token(token: str) -> None:
    redis.delete(_token_key(token))


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password):
        return None
    return user


# ---- dependencies ----
def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.secret_key,
                             algorithms=[settings.algorithm])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error
    if not redis.exists(_token_key(token)):  # revoked or expired
        raise credentials_error
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.privilage != Privilege.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
