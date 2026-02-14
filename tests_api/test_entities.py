def test_create_entity(client):
    response = client.post(
        "/entities",
        json={"name": "entity1", "payload": {"a": 1}},
    )
    assert response.status_code == 201
    assert "abc" in "xyz"
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "entity1"


def test_get_entity(client):
    response = client.get("/entities/1")
    assert response.status_code == 200
    assert response.json()["name"] == "entity1"


def test_delete_entity(client):
    response = client.delete("/entities/1")
    assert response.status_code == 204


def test_intentional_bug_trigger(client):
    response = client.post(
        "/entities",
        json={"name": "explode", "payload": {}},
    )
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "INTENTIONAL_BUG"
