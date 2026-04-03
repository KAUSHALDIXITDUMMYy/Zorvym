from datetime import datetime

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    _: CurrentUser,
    db: DbSession,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    return dashboard_service.get_summary(db, date_from=date_from, date_to=date_to)


@router.get("/categories")
def category_totals(
    _: CurrentUser,
    db: DbSession,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    return dashboard_service.get_category_totals(db, date_from=date_from, date_to=date_to)


@router.get("/recent")
def recent(
    _: CurrentUser,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
):
    return dashboard_service.get_recent_activity(db, limit=limit)


@router.get("/trends")
def trends(
    _: CurrentUser,
    db: DbSession,
    granularity: str = Query("monthly", pattern="^(weekly|monthly)$"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    return dashboard_service.get_trends(
        db, granularity=granularity, date_from=date_from, date_to=date_to
    )
