from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.crud import records as records_crud
from app.deps import DbSession, RequireAdmin, RequireAnalystOrAdmin
from app.models import EntryType, FinancialRecord
from app.schemas import (
    FinancialRecordCreate,
    FinancialRecordResponse,
    FinancialRecordUpdate,
    PaginatedRecords,
)

router = APIRouter(prefix="/records", tags=["records"])


def _parse_type(value: str | None) -> EntryType | None:
    if value is None:
        return None
    try:
        return EntryType(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="type must be 'income' or 'expense'",
        )


@router.get("", response_model=PaginatedRecords)
def list_records(
    _: RequireAnalystOrAdmin,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    category: str | None = Query(None, min_length=1, max_length=120),
    type: str | None = Query(None, description="income or expense"),
) -> PaginatedRecords:
    entry_type = _parse_type(type)
    items, total = records_crud.list_records(
        db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        category=category,
        entry_type=entry_type,
    )
    return PaginatedRecords(items=items, total=total, skip=skip, limit=limit)


@router.get("/{record_id}", response_model=FinancialRecordResponse)
def get_record(
    _: RequireAnalystOrAdmin,
    db: DbSession,
    record_id: int,
) -> FinancialRecord:
    rec = records_crud.get_record(db, record_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return rec


@router.post("", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    user: RequireAdmin,
    db: DbSession,
    body: FinancialRecordCreate,
) -> FinancialRecord:
    return records_crud.create_record(db, body, created_by_id=user.id)


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    _: RequireAdmin,
    db: DbSession,
    record_id: int,
    body: FinancialRecordUpdate,
) -> FinancialRecord:
    rec = records_crud.get_record(db, record_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return records_crud.update_record(db, rec, body)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    _: RequireAdmin,
    db: DbSession,
    record_id: int,
) -> None:
    rec = records_crud.get_record(db, record_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    records_crud.delete_record(db, rec)
