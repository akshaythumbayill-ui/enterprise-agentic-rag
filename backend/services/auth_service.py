import os
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database_service import get_user_by_id

security = HTTPBearer()
password_hasher = PasswordHasher()


def hash_password(password: str):
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str):
    try:
        if password_hash.startswith("$argon2"):
            return password_hasher.verify(password_hash, password)
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("ascii"),
        )
    except (ValueError, UnicodeError, Exception):
        return False


def create_access_token(user_id: int, username: str):
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is missing from .env.")

    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise RuntimeError("JWT authentication is not configured.")

        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=["HS256"],
        )

        user_id = int(payload["sub"])

    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account was not found.",
        )

    return user