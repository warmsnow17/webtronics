import pytest
from starlette.testclient import TestClient
from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.auth import get_password_hash

client = TestClient(app)

test_user_data = {
    "username": "testuser",
    "password": "testpassword"
}


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    hashed_password = get_password_hash(test_user_data["password"])
    test_user = User(username=test_user_data["username"], hashed_password=hashed_password)
    test_db.add(test_user)
    test_db.commit()
    return test_user


def test_create_user(test_db):
    response = client.post("/api/create_user/", json=test_user_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert "id" in data


def test_create_user_existing_username(test_db, test_user):
    response = client.post("/api/create_user/", json=test_user_data)
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Username already registered"}


def test_token(test_db, test_user):
    response = client.post("/api/login/", json=test_user_data)
    assert response.status_code == 200, response.text
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


def test_token_invalid_password(test_db, test_user):
    response = client.post("/api/login", json={**test_user_data, "password": "wrongpassword"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Incorrect username or password"}


def test_read_users_me(test_db, test_user):
    response = client.post("/api/login", json=test_user_data)
    token = response.json()["access_token"]
    response = client.get("/api/users/me/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert "id" in data


def test_read_users_me_no_token(test_db, test_user):
    response = client.get("/api/users/me/")
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Not authenticated"}
