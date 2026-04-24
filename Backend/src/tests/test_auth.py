from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_registro_ok():
    response = client.post("/registro", json={
        "name": "Test User",
        "email": "test@example.com",
        "contrasenas": "123456"
    })

    assert response.status_code == 200
    assert response.json()["ok"] == True


def test_registro_duplicado():

    client.post("/registro", json={
        "name": "Test User",
        "email": "dup@example.com",
        "contrasenas": "123456"
    })

    # segundo intento
    response = client.post("/registro", json={
        "name": "Test User",
        "email": "dup@example.com",
        "contrasenas": "123456"
    })

    assert response.status_code == 400
    assert "Correo ya registrado" in response.text


def test_login_ok():
    # registrar primero
    client.post("/registro", json={
        "name": "Login User",
        "email": "login@example.com",
        "contrasenas": "123456"
    })

    # login
    response = client.post("/login", json={
        "email": "login@example.com",
        "contrasena": "123456"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    # registrar
    client.post("/registro", json={
        "name": "Wrong Pass",
        "email": "wrong@example.com",
        "contrasenas": "123456"
    })

    # login incorrecto
    response = client.post("/login", json={
        "email": "wrong@example.com",
        "contrasena": "badpass"
    })

    assert response.status_code == 400


def test_obtener_llave():
    # registrar
    r = client.post("/registro", json={
        "name": "Key User",
        "email": "key@example.com",
        "contrasenas": "123456"
    })

    # obtener id manual (hack rápido)
    login = client.post("/login", json={
        "email": "key@example.com",
        "contrasena": "123456"
    })

    assert login.status_code == 200

    response = client.get("/users/1/key")

    assert response.status_code in [200, 404]