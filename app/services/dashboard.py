from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import EntryType, FinancialRecord
from app.schemas import CategoryTotal, DashboardSummary, RecentActivityItem, TrendPoint


def get_summary(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> DashboardSummary:
    base = select(
        func.coalesce(
            func.sum(case((FinancialRecord.type == EntryType.income, FinancialRecord.amount), else_=0.0)),
            0.0,
        ).label("total_income"),
        func.coalesce(
            func.sum(case((FinancialRecord.type == EntryType.expense, FinancialRecord.amount), else_=0.0)),
            0.0,
        ).label("total_expenses"),
        func.count(FinancialRecord.id).label("record_count"),
    )
    if date_from is not None:
        base = base.where(FinancialRecord.date >= date_from)
    if date_to is not None:
        base = base.where(FinancialRecord.date <= date_to)

    row = db.execute(base).one()
    income = float(row.total_income or 0)
    expenses = float(row.total_expenses or 0)
    return DashboardSummary(
        total_income=income,
        total_expenses=expenses,
        net_balance=income - expenses,
        record_count=int(row.record_count or 0),
    )


def get_category_totals(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[CategoryTotal]:
    stmt = (
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(FinancialRecord.category, FinancialRecord.type)
    )
    if date_from is not None:
        stmt = stmt.where(FinancialRecord.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(FinancialRecord.date <= date_to)

    return [
        CategoryTotal(category=r.category, type=r.type, total=float(r.total or 0))
        for r in db.execute(stmt).all()
    ]


def get_recent_activity(db: Session, limit: int = 10) -> list[RecentActivityItem]:
    stmt = (
        select(FinancialRecord)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .limit(min(max(limit, 1), 50))
    )
    rows = db.scalars(stmt).all()
    return [
        RecentActivityItem(
            id=r.id,
            amount=r.amount,
            type=r.type,
            category=r.category,
            date=r.date,
            notes=r.notes,
        )
        for r in rows
    ]


def get_trends(
    db: Session,
    *,
    granularity: str = "monthly",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[TrendPoint]:
    """Aggregate income/expense by calendar week (ISO) or month using SQLite strftime."""
    if granularity not in ("weekly", "monthly"):
        granularity = "monthly"

    if granularity == "monthly":
        period_expr = func.strftime("%Y-%m", FinancialRecord.date)
    else:
        period_expr = func.strftime("%Y-W%W", FinancialRecord.date)

    stmt = (
        select(
            period_expr.label("period"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == EntryType.income, FinancialRecord.amount), else_=0.0)),
                0.0,
            ).label("income"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == EntryType.expense, FinancialRecord.amount), else_=0.0)),
                0.0,
            ).label("expense"),
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )
    if date_from is not None:
        stmt = stmt.where(FinancialRecord.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(FinancialRecord.date <= date_to)

    out: list[TrendPoint] = []
    for r in db.execute(stmt).all():
        inc = float(r.income or 0)
        exp = float(r.expense or 0)
        out.append(
            TrendPoint(period=str(r.period), income=inc, expense=exp, net=inc - exp),
        )
    return out


def default_range_last_year() -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    start = end - timedelta(days=365)
    return start, end
