from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.crud import users as users_crud
from app.deps import CurrentUser, DbSession, RequireAdmin
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_me(user: CurrentUser) -> User:
    return user


@router.get("", response_model=list[UserResponse])
def list_users(
    _: RequireAdmin,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[User]:
    rows, _ = users_crud.list_users(db, skip=skip, limit=limit)
    return rows


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(_: RequireAdmin, db: DbSession, body: UserCreate) -> User:
    if users_crud.get_by_email(db, str(body.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if users_crud.get_by_username(db, body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    try:
        return users_crud.create_user(db, body)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create user (constraint violation)",
        )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    _: RequireAdmin,
    db: DbSession,
    user_id: int,
    body: UserUpdate,
) -> User:
    user = users_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.email is not None:
        existing = users_crud.get_by_email(db, str(body.email))
        if existing and existing.id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    if body.username is not None:
        existing = users_crud.get_by_username(db, body.username)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use")
    try:
        return users_crud.update_user(db, user, body)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update user (constraint violation)",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(_: RequireAdmin, db: DbSession, user_id: int) -> None:
    user = users_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    users_crud.delete_user(db, user)
