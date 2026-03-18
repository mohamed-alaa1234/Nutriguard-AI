from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_signup_and_login_flow(tmp_path, monkeypatch):
    response = client.post(
        "/auth/signup",
        json={
            "email": "user@example.com",
            "full_name": "Test User",
            "password": "strongpassword",
        },
    )
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "user@example.com"

    response = client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
            "password": "strongpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    response = client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    me = response.json()
    assert me["email"] == "user@example.com"

