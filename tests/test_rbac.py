from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> str:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_viewer_dashboard_ok_records_forbidden():
    t = _login("viewer", "viewer123")
    h = {"Authorization": f"Bearer {t}"}
    assert client.get("/dashboard/summary", headers=h).status_code == 200
    assert client.get("/records", headers=h).status_code == 403


def test_analyst_read_only_records():
    t = _login("analyst", "analyst123")
    h = {"Authorization": f"Bearer {t}"}
    assert client.get("/records", headers=h).status_code == 200
    r = client.post(
        "/records",
        headers=h,
        json={
            "amount": 1.0,
            "type": "income",
            "category": "test",
            "date": "2026-01-15T12:00:00",
        },
    )
    assert r.status_code == 403


def test_admin_can_create_record():
    t = _login("admin", "admin123")
    h = {"Authorization": f"Bearer {t}"}
    r = client.post(
        "/records",
        headers=h,
        json={
            "amount": 2.5,
            "type": "expense",
            "category": "test",
            "date": "2026-02-01T12:00:00",
            "notes": "pytest",
        },
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    assert client.delete(f"/records/{rid}", headers=h).status_code == 204
