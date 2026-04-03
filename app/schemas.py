from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import EntryType, UserRole


class RoleEnum(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class EntryTypeEnum(str, Enum):
    income = "income"
    expense = "expense"


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int | None = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


# --- Users ---
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=100)
    role: RoleEnum = RoleEnum.viewer
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=200)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=2, max_length=100)
    role: RoleEnum | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=200)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime


# --- Financial records ---
class FinancialRecordBase(BaseModel):
    amount: float = Field(..., gt=0, description="Positive amount; type distinguishes income vs expense")
    type: EntryTypeEnum
    category: str = Field(..., min_length=1, max_length=120)
    date: datetime
    notes: str | None = Field(None, max_length=5000)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("category cannot be empty")
        return s


class FinancialRecordCreate(FinancialRecordBase):
    pass


class FinancialRecordUpdate(BaseModel):
    amount: float | None = Field(None, gt=0)
    type: EntryTypeEnum | None = None
    category: str | None = Field(None, min_length=1, max_length=120)
    date: datetime | None = None
    notes: str | None = Field(None, max_length=5000)

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("category cannot be empty")
        return s

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field must be provided for update")
        return self


class FinancialRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: EntryType
    category: str
    date: datetime
    notes: str | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime


class PaginatedRecords(BaseModel):
    items: list[FinancialRecordResponse]
    total: int
    skip: int
    limit: int


# --- Dashboard ---
class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    record_count: int


class CategoryTotal(BaseModel):
    category: str
    type: EntryType
    total: float


class TrendPoint(BaseModel):
    period: str
    income: float
    expense: float
    net: float


class RecentActivityItem(BaseModel):
    id: int
    amount: float
    type: EntryType
    category: str
    date: datetime
    notes: str | None = None
