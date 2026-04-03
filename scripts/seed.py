"""
Create demo users and sample financial records.
Run from project root: python -m scripts.seed
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import EntryType, FinancialRecord, User, UserRole
from app.security import hash_password


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalars(select(User)).first() is not None:
            print("Database already has users; skipping seed.")
            return

        users_spec = [
            ("admin@example.com", "admin", "admin123", UserRole.admin),
            ("analyst@example.com", "analyst", "analyst123", UserRole.analyst),
            ("viewer@example.com", "viewer", "viewer123", UserRole.viewer),
        ]
        created: list[User] = []
        for email, username, password, role in users_spec:
            u = User(
                email=email,
                username=username,
                hashed_password=hash_password(password),
                role=role,
                is_active=True,
            )
            db.add(u)
            created.append(u)
        db.flush()

        admin = created[0]
        today = datetime.now(timezone.utc).replace(tzinfo=None, hour=12, minute=0, second=0, microsecond=0)
        samples = [
            (5000.0, EntryType.income, "Salary", today - timedelta(days=60), "Monthly salary"),
            (120.5, EntryType.expense, "Food", today - timedelta(days=58), "Groceries"),
            (800.0, EntryType.income, "Freelance", today - timedelta(days=45), "Project A"),
            (200.0, EntryType.expense, "Transport", today - timedelta(days=40), "Fuel"),
            (1500.0, EntryType.expense, "Rent", today - timedelta(days=30), "Apartment"),
            (300.0, EntryType.income, "Interest", today - timedelta(days=14), "Savings account"),
            (75.0, EntryType.expense, "Food", today - timedelta(days=7), "Dining out"),
        ]
        for amount, typ, category, dt, notes in samples:
            db.add(
                FinancialRecord(
                    amount=amount,
                    type=typ,
                    category=category,
                    date=dt,
                    notes=notes,
                    created_by_id=admin.id,
                )
            )
        db.commit()
        print("Seeded users (password in parentheses):")
        for email, username, password, role in users_spec:
            print(f"  {username} / {password}  role={role.value}  {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
