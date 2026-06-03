from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid
from datetime import datetime

import pytest

from src import app
from src.tags import routers as tags_routes
from src.auth.dependencies import get_current_user, get_tag_service
from src.errors import TagAlreadyExists, TagNotFound


prefix = "/api/V1/tags"


def override_tag_service(fake_tag_service):
    app.dependency_overrides[get_tag_service] = lambda: fake_tag_service


def remove_tag_service_override():
    app.dependency_overrides.pop(get_tag_service, None)


# Retrieve all tags as an authenticated user
def test_get_all_tags_success(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    fake_tag_service.get_tags = AsyncMock(return_value=[{"uid": str(uuid.uuid4()), "name": "fiction", "created_at": "2024-01-01T00:00:00"}])

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    resp = test_client.get(f"{prefix}/")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Create a new tag successfully (201)
def test_add_tag_success(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    uid = str(uuid.uuid4())
    fake_tag_service.add_tag = AsyncMock(return_value={"uid": uid, "name": "sci-fi", "created_at": "2024-01-01T00:00:00"})

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    resp = test_client.post(f"{prefix}/", json={"name": "sci-fi"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "sci-fi"

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Creating an existing tag returns conflict (403)
def test_add_tag_conflict(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    fake_tag_service.add_tag = AsyncMock(side_effect=TagAlreadyExists())

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    resp = test_client.post(f"{prefix}/", json={"name": "existing"})

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "tag_exists"

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Add tags to a book and return the updated book
def test_add_tags_to_book_success(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    # Return a BookModel-like dict
    book = {
        "uid": str(uuid.uuid4()),
        "title": "B",
        "author": "Auth",
        "publisher": "Pub",
        "published_date": "2020-01-01",
        "page_count": 100,
        "language": "en",
        "user_uid": str(uuid.uuid4()),
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    fake_tag_service.add_tags_to_book = AsyncMock(return_value=book)

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    book_uid = str(uuid.uuid4())
    resp = test_client.post(f"{prefix}/book/{book_uid}/tags", json={"tags": [{"name": "tag1"}]})

    assert resp.status_code == 200
    assert resp.json()["title"] == "B"

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Update an existing tag successfully
def test_update_tag_success(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    uid = str(uuid.uuid4())
    fake_tag_service.update_tag = AsyncMock(return_value={"uid": uid, "name": "updated", "created_at": "2024-01-01T00:00:00"})

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="user", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    resp = test_client.put(f"{prefix}/{uid}", json={"name": "updated"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "updated"

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Delete a tag as admin (204)
def test_delete_tag_success(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    fake_tag_service.delete_tag = AsyncMock(return_value=None)

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="admin", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    uid = str(uuid.uuid4())
    resp = test_client.delete(f"{prefix}/{uid}")

    assert resp.status_code == 204

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()


# Deleting a non-existent tag returns 404
def test_delete_tag_not_found(test_client, fake_session):
    fake_tag_service = SimpleNamespace()
    fake_tag_service.delete_tag = AsyncMock(side_effect=TagNotFound())

    override_tag_service(fake_tag_service)

    user = SimpleNamespace(role="admin", is_verified=True)
    app.dependency_overrides[get_current_user] = lambda: user

    uid = str(uuid.uuid4())
    resp = test_client.delete(f"{prefix}/{uid}")

    assert resp.status_code == 404
    assert resp.json()["error_code"] == "tag_not_found"

    app.dependency_overrides.pop(get_current_user, None)
    remove_tag_service_override()
