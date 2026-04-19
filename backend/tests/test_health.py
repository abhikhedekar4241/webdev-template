def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_has_status_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_body_has_db_ok(client):
    response = client.get("/health")
    data = response.json()
    assert data["db"] == "ok"


def test_health_has_request_id_header(client):
    response = client.get("/health")
    assert "x-request-id" in response.headers
