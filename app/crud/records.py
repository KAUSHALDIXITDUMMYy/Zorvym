from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import EntryType, FinancialRecord
from app.schemas import FinancialRecordCreate, FinancialRecordUpdate


def _apply_filters(
    stmt,
    *,
    date_from: datetime | None,
    date_to: datetime | None,
    category: str | None,
    entry_type: EntryType | None,
):
    if date_from is not None:
        stmt = stmt.where(FinancialRecord.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(FinancialRecord.date <= date_to)
    if category is not None:
        stmt = stmt.where(FinancialRecord.category == category)
    if entry_type is not None:
        stmt = stmt.where(FinancialRecord.type == entry_type)
    return stmt


def list_records(
    db: Session,
    *,
    skip: int,
    limit: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    category: str | None = None,
    entry_type: EntryType | None = None,
) -> tuple[list[FinancialRecord], int]:
    filtered = _apply_filters(
        select(FinancialRecord),
        date_from=date_from,
        date_to=date_to,
        category=category,
        entry_type=entry_type,
    )
    subq = filtered.subquery()
    total = db.scalar(select(func.count()).select_from(subq)) or 0

    stmt = _apply_filters(
        select(FinancialRecord),
        date_from=date_from,
        date_to=date_to,
        category=category,
        entry_type=entry_type,
    )
    stmt = stmt.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).offset(skip).limit(limit)
    rows = db.scalars(stmt).all()
    return list(rows), int(total)


def get_record(db: Session, record_id: int) -> FinancialRecord | None:
    return db.get(FinancialRecord, record_id)


def create_record(db: Session, data: FinancialRecordCreate, created_by_id: int | None) -> FinancialRecord:
    rec = FinancialRecord(
        amount=data.amount,
        type=EntryType(data.type.value),
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by_id=created_by_id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def update_record(db: Session, record: FinancialRecord, data: FinancialRecordUpdate) -> FinancialRecord:
    if data.amount is not None:
        record.amount = data.amount
    if data.type is not None:
        record.type = EntryType(data.type.value)
    if data.category is not None:
        record.category = data.category
    if data.date is not None:
        record.date = data.date
    if data.notes is not None:
        record.notes = data.notes
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record: FinancialRecord) -> None:
    db.delete(record)
    db.commit()
