# File: tests/test_auth.py


def test_register_and_login(client):
    resp = client.post(
        "/register",
        json={"username": "bob", "email": "bob@example.com", "password": "outra-senha"},
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "bob"

    resp = client.post("/token", data={"username": "bob", "password": "outra-senha"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_fails(client):
    client.post(
        "/register",
        json={"username": "carol", "email": "carol@example.com", "password": "certa"},
    )
    resp = client.post("/token", data={"username": "carol", "password": "errada"})
    assert resp.status_code == 401


def test_duplicate_register_fails(client):
    payload = {"username": "dave", "email": "dave@example.com", "password": "x"}
    client.post("/register", json=payload)
    resp = client.post("/register", json=payload)
    assert resp.status_code == 409


def test_protected_endpoint_requires_token(client):
    resp = client.get("/history")
    assert resp.status_code == 401
