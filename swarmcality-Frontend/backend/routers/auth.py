from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from models.user import User
from services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _user_out(user: User) -> dict:
    return {"id": str(user.id), "email": user.email, "name": user.name}


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    if await User.find_one(User.email == body.email):
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        email=body.email.lower().strip(),
        name=body.name.strip(),
        password_hash=hash_password(body.password),
    )
    await user.insert()
    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=_user_out(user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    user = await User.find_one(User.email == body.email.lower().strip())
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token, user=_user_out(user))


from fastapi import Depends as _Depends
from services.auth_service import get_current_user as _get_current_user


@router.get("/me")
async def me(current_user: User = _Depends(_get_current_user)):
    return _user_out(current_user)
