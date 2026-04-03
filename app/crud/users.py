from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.schemas import UserCreate, UserUpdate
from app.security import hash_password


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalars(select(User).where(User.username == username)).first()


def list_users(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)).all()
    return list(rows), int(total)


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role=UserRole(data.role.value),
        is_active=data.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.email is not None:
        user.email = str(data.email)
    if data.username is not None:
        user.username = data.username
    if data.role is not None:
        user.role = UserRole(data.role.value)
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
