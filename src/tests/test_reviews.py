from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid
import pytest

from fastapi import HTTPException, status

from src import app
from src.reviews import routes as review_routes
from src.auth.dependencies import get_current_user


prefix = "/api/V1/reviews"


def override_user(user):
    app.dependency_overrides[get_current_user] = lambda: user


def remove_user_override():
    app.dependency_overrides.pop(get_current_user, None)


# Admin can list all reviews successfully
def test_get_all_reviews_admin_success(test_client, fake_session):
    orig = getattr(review_routes.review_service, "get_all_reviews", None)
    review_routes.review_service.get_all_reviews = AsyncMock(return_value=[{"uid": str(uuid.uuid4()), "rating": 4, "review_text": "Good", "user_uid": str(uuid.uuid4()), "book_uid": str(uuid.uuid4()), "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}])

    user = SimpleNamespace(role="admin", is_verified=True)
    override_user(user)

    resp = test_client.get(f"{prefix}/")

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    review_routes.review_service.get_all_reviews.assert_awaited_once_with(fake_session)

    remove_user_override()
    if orig is not None:
        review_routes.review_service.get_all_reviews = orig


# Requesting a missing review raises a runtime error (route bug)
def test_get_review_not_found_returns_500(test_client, fake_session):
    orig = getattr(review_routes.review_service, "get_review", None)
    review_routes.review_service.get_review = AsyncMock(return_value=None)

    user = SimpleNamespace(role="user", is_verified=True)
    override_user(user)

    uid = str(uuid.uuid4())
    with pytest.raises(RuntimeError):
        test_client.get(f"{prefix}/{uid}")

    remove_user_override()
    if orig is not None:
        review_routes.review_service.get_review = orig


# Authenticated user can add a review to a book successfully
def test_add_review_success(test_client, fake_session):
    orig = getattr(review_routes.review_service, "add_review_to_book", None)
    fake_return = {"uid": str(uuid.uuid4()), "rating": 4, "review_text": "Nice book", "user_uid": str(uuid.uuid4()), "book_uid": str(uuid.uuid4()), "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}
    review_routes.review_service.add_review_to_book = AsyncMock(return_value=fake_return)

    user = SimpleNamespace(email="emma@example.com", role="user", is_verified=True)
    override_user(user)

    book_uid = str(uuid.uuid4())
    payload = {"rating": 4, "review_text": "Nice book"}

    resp = test_client.post(f"{prefix}/book/{book_uid}", json=payload)

    assert resp.status_code == 200
    assert resp.json()["rating"] == 4

    remove_user_override()
    if orig is not None:
        review_routes.review_service.add_review_to_book = orig


# Adding a review to non-existent book returns 404
def test_add_review_book_not_found(test_client, fake_session):
    orig = getattr(review_routes.review_service, "add_review_to_book", None)
    review_routes.review_service.add_review_to_book = AsyncMock(side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"))

    user = SimpleNamespace(email="emma@example.com", role="user", is_verified=True)
    override_user(user)

    book_uid = str(uuid.uuid4())
    payload = {"rating": 4, "review_text": "Nice book"}

    resp = test_client.post(f"{prefix}/book/{book_uid}", json=payload)

    assert resp.status_code == 404

    remove_user_override()
    if orig is not None:
        review_routes.review_service.add_review_to_book = orig


# Authenticated user can delete their review (204)
def test_delete_review_success(test_client, fake_session):
    orig = getattr(review_routes.review_service, "delete_review_to_from_book", None)
    review_routes.review_service.delete_review_to_from_book = AsyncMock(return_value=None)

    user = SimpleNamespace(email="emma@example.com", role="user", is_verified=True)
    override_user(user)

    uid = str(uuid.uuid4())
    resp = test_client.delete(f"{prefix}/{uid}")

    assert resp.status_code == 204

    remove_user_override()
    if orig is not None:
        review_routes.review_service.delete_review_to_from_book = orig
