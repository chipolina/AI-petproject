import pytest


@pytest.mark.component("api")
def test_login_success(client):
    response = client.post(
        "/login",
        json={"username": "denis", "password": "1234"},
    )
    assert response.status_code == 203
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.component("api")
def test_login_blocked_user(client):
    response = client.post(
        "/login",
        json={"username": "blocked", "password": "1234"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "USER_BLOCKED"
