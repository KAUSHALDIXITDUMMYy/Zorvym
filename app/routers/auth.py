from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import users as users_crud
from app.deps import DbSession
from app.schemas import LoginRequest, Token
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: DbSession) -> Token:
    user = users_crud.get_by_username(db, body.username)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=token)
