def test_health_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_unknown_route_returns_404(client):
    assert client.get("/api/v1/nope").status_code == 404
