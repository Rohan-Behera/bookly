from fastapi import APIRouter, status, Depends
from .schemas import BookModel, BookUpdateModel, BookCreateModel, BookDetailModel
from typing import List
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
import uuid
from src.auth.dependencies import RoleChecker, get_current_user, get_book_service
from src.errors import BookNotFound

book_router = APIRouter()


@book_router.get("/", response_model=List[BookModel])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    return await book_service.get_all_books(session)


@book_router.get("/user/{user_uid}", response_model=List[BookModel])
async def get_user_books_by_uid(
    user_uid: str,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    return await book_service.get_user_books(user_uid, session)


@book_router.get("/user-books", response_model=List[BookModel])
async def get_my_books(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    return await book_service.get_user_books(str(current_user.uid), session)


@book_router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookModel)
async def create_a_book(
    book_data: BookCreateModel,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    return await book_service.create_books(book_data, str(current_user.uid), session)


@book_router.get("/{book_uid}", response_model=BookDetailModel)
async def get_book(
    book_uid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    book = await book_service.get_book_id(book_uid, session)
    if not book:
        raise BookNotFound()
    return book


@book_router.patch("/{book_uid}")
async def update_book(
    book_uid: uuid.UUID,
    book_update_data: BookUpdateModel,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    updated_book = await book_service.update_book(book_uid, book_update_data, session)
    if not updated_book:
        raise BookNotFound()
    return updated_book


@book_router.delete("/{book_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_uid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["admin", "user"])),
    book_service: BookService = Depends(get_book_service),
):
    book_to_delete = await book_service.delete_book(book_uid, session)
    if not book_to_delete:
        raise BookNotFound()
