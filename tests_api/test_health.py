def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 600
    assert response.json() == {"status": "ok"}
