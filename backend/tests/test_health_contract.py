def test_health_contract(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_current_user_contract(client) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant"]["plan"] == "standard_ops"
    assert "owner" in payload["roles"]
