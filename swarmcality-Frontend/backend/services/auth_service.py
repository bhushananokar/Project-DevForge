from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings
from models.user import User

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id: Optional[str] = payload.get("sub")
        if not user_id:
            raise exc
    except JWTError:
        raise exc

    user = await User.get(user_id)
    if not user:
        raise exc
    return user
