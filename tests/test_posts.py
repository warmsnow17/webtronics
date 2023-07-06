import pytest
from starlette.testclient import TestClient

from app.main import app
from app.models.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.auth import get_password_hash, create_access_token
from app.models.posts import Post as DBPost
from app.schemas.schemas import PostCreate

client = TestClient(app)

test_user_data = {
    "username": "testuser",
    "password": "testpassword"
}

test_user2_data = {
    "username": "testuser2",
    "password": "testpassword2"
}
test_post_data = PostCreate(title="Test title", content="Test content")


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


@pytest.fixture
def test_post(test_db, test_user):
    test_post = DBPost(title=test_post_data.title, content=test_post_data.content, user_id=test_user.id)
    test_db.add(test_post)
    test_db.commit()
    return test_post


@pytest.fixture
def test_user2(test_db):
    hashed_password = get_password_hash(test_user2_data["password"])
    test_user2 = User(username=test_user2_data["username"], hashed_password=hashed_password)
    test_db.add(test_user2)
    test_db.commit()
    return test_user2


def test_create_post(test_db, test_user):
    access_token = create_access_token(data={"sub": test_user.username})
    response = client.post("/api/posts/", headers={"Authorization": f"Bearer {access_token}"},
                           json=test_post_data.dict())
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == test_post_data.title
    assert data["content"] == test_post_data.content
    assert "id" in data
    assert "user_id" in data


def test_get_posts(test_db, test_user):
    test_post_data = {"title": "Test Title", "content": "Test Content"}
    access_token = create_access_token(data={"sub": test_user.username})
    response_post = client.post("/api/posts/", headers={"Authorization": f"Bearer {access_token}"}, json=test_post_data)
    response_get = client.get("/api/posts/", headers={"Authorization": f"Bearer {access_token}"})
    assert response_get.status_code == 200, response_get.text
    assert isinstance(response_get.json(), list)
    assert len(response_get.json()) == 1


def test_get_post_by_id(test_db, test_user):
    test_post_data = {"title": "Test Title", "content": "Test Content"}
    access_token = create_access_token(data={"sub": test_user.username})
    response = client.post("/api/posts/", headers={"Authorization": f"Bearer {access_token}"}, json=test_post_data)
    assert response.status_code == 200, response.text
    post_id = response.json().get("id")
    response = client.get(f"/api/posts/{post_id}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("title") == "Test Title"
    assert data.get("content") == "Test Content"


def test_update_post(test_db, test_user):
    test_post_data = {"title": "Test Title", "content": "Test Content"}
    access_token = create_access_token(data={"sub": test_user.username})
    response = client.post("/api/posts/", headers={"Authorization": f"Bearer {access_token}"}, json=test_post_data)
    assert response.status_code == 200, response.text
    post_id = response.json().get("id")
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put(f"/api/posts/{post_id}", headers={"Authorization": f"Bearer {access_token}"},
                          json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("title") == "Updated Title"
    assert data.get("content") == "Updated Content"


def test_delete_post(test_db, test_user):
    test_post_data = {"title": "Test Title", "content": "Test Content"}
    access_token = create_access_token(data={"sub": test_user.username})
    response = client.post("/api/posts/", headers={"Authorization": f"Bearer {access_token}"}, json=test_post_data)
    assert response.status_code == 200, response.text
    post_id = response.json().get("id")
    response = client.delete(f"/api/posts/{post_id}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    response = client.get(f"/api/posts/{post_id}", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404, response.text


def test_like_own_post(test_db, test_user, test_post):
    access_token = create_access_token(data={"sub": test_user.username})
    response = client.post(f"/api/posts/{test_post.id}/like", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 404, response.text


def test_like_post(test_db, test_user, test_user2, test_post):
    access_token = create_access_token(data={"sub": test_user2.username})
    response = client.post(f"/api/posts/{test_post.id}/like", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data
    assert data["user_id"] == test_user2.id
    assert data["post_id"] == test_post.id


def test_unlike_post(test_db, test_user, test_user2, test_post):
    access_token = create_access_token(data={"sub": test_user2.username})
    response = client.post(f"/api/posts/{test_post.id}/like", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    response = client.delete(f"/api/posts/{test_post.id}/unlike", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data
    assert data["user_id"] == test_user2.id
    assert data["post_id"] == test_post.id
