from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

from src import app
from src.books import routes as book_routes
from src.auth.dependencies import get_current_user, get_book_service


books_prefix = "/api/V1/books"


def override_book_service(fake_book_service):
    app.dependency_overrides[get_book_service] = lambda: fake_book_service


def remove_book_service_override():
    app.dependency_overrides.pop(get_book_service, None)


# Get all books (public for authenticated users)
def test_get_all_books(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    fake_book_service.get_all_books = AsyncMock(return_value=[{
        "uid": str(uuid.uuid4()),
        "title": "A",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 123,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }])

    override_book_service(fake_book_service)

    # provide a verified user for RoleChecker
    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.get(f"{books_prefix}/")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Get books for a particular user by uid
def test_get_user_books_by_uid(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    fake_book_service.get_user_books = AsyncMock(return_value=[{
        "uid": str(uuid.uuid4()),
        "title": "B",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 200,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }])

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    target_uid = "user-123"
    resp = test_client.get(f"{books_prefix}/user/{target_uid}")

    assert resp.status_code == 200
    fake_book_service.get_user_books.assert_awaited_once_with(target_uid, fake_session)

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Get current user's books via /user-books
def test_get_my_books(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    fake_book_service.get_user_books = AsyncMock(return_value=[{
        "uid": str(uuid.uuid4()),
        "title": "C",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 150,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }])

    override_book_service(fake_book_service)

    my_uid = str(uuid.uuid4())
    user_obj = SimpleNamespace(uid=my_uid, role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.get(f"{books_prefix}/user-books")

    assert resp.status_code == 200
    fake_book_service.get_user_books.assert_awaited_once_with(str(my_uid), fake_session)

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Create a new book for the current user
def test_create_a_book(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    owner_id = str(uuid.uuid4())
    created = {
        "uid": str(uuid.uuid4()),
        "title": "New",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 100,
        "language": "en",
        "user_uid": owner_id,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    fake_book_service.create_books = AsyncMock(return_value=created)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=owner_id, role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    payload = {"title": "New", "author": "Auth", "publisher": "Pub", "published_date": "2020-01-01", "page_count": 100, "language": "en"}
    resp = test_client.post(f"{books_prefix}/", json=payload)

    assert resp.status_code == 201
    assert resp.json()["title"] == "New"
    fake_book_service.create_books.assert_awaited_once()

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Retrieve a book by uid when it exists
def test_get_book_found(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    detail = {
        "uid": str(book_uid),
        "title": "Found",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 321,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "reviews": [],
        "tags": [],
    }
    fake_book_service.get_book_id = AsyncMock(return_value=detail)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.get(f"{books_prefix}/{book_uid}")

    assert resp.status_code == 200
    assert resp.json()["uid"] == str(book_uid)

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Retrieving a non-existent book returns 404
def test_get_book_not_found(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    fake_book_service.get_book_id = AsyncMock(return_value=None)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.get(f"{books_prefix}/{book_uid}")

    assert resp.status_code == 404
    assert resp.json()["error_code"] == "book_not_found"

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Update an existing book successfully
def test_update_book_success(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    updated = {
        "uid": str(book_uid),
        "title": "Updated",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 250,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    fake_book_service.update_book = AsyncMock(return_value=updated)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    payload = {"title": "Updated", "author": "Auth", "publisher": "Pub", "page_count": 250, "language": "en"}
    resp = test_client.patch(f"{books_prefix}/{book_uid}", json=payload)

    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Update a non-existent book returns 404
def test_update_book_not_found(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    fake_book_service.update_book = AsyncMock(return_value=None)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    payload = {"title": "Nope", "author": "Auth", "publisher": "Pub", "page_count": 10, "language": "en"}
    resp = test_client.patch(f"{books_prefix}/{book_uid}", json=payload)

    assert resp.status_code == 404
    assert resp.json()["error_code"] == "book_not_found"

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Delete an existing book returns 204
def test_delete_book_success(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    fake_book_service.delete_book = AsyncMock(return_value=True)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.delete(f"{books_prefix}/{book_uid}")

    assert resp.status_code == 204

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()


# Deleting a non-existent book returns 404
def test_delete_book_not_found(test_client, fake_session):
    fake_book_service = SimpleNamespace()
    book_uid = uuid.uuid4()
    fake_book_service.delete_book = AsyncMock(return_value=False)

    override_book_service(fake_book_service)

    user_obj = SimpleNamespace(uid=str(uuid.uuid4()), role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user_obj

    resp = test_client.delete(f"{books_prefix}/{book_uid}")

    assert resp.status_code == 404
    assert resp.json()["error_code"] == "book_not_found"

    app.dependency_overrides.pop(get_current_user, None)
    remove_book_service_override()
