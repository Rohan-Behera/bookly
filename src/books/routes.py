from src.books.book_data import books
from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from .schemas import BookModel, BookUpdateModel, BookCreateModel, BookDetailModel
from typing import List
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
import uuid
from src.auth.dependencies import AccessTokenBearer, RoleChecker
from src.errors import BookNotFound

book_router = APIRouter()
book_service = BookService()
jwt_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(['admin','user']))

@book_router.get('/', response_model=List[BookModel], dependencies=[role_checker])
async def get_all_books(session: AsyncSession = Depends(get_session), 
                        token_details: dict = Depends(jwt_bearer)):    
    books = await book_service.get_all_books(session)
    return books

@book_router.get('/user/{user_uid}', response_model=List[BookModel], dependencies=[role_checker])
async def get_user_books(user_uid: str,
                        session: AsyncSession = Depends(get_session), 
                        token_details: dict = Depends(jwt_bearer)):
    books = await book_service.get_user_books(user_uid, session)
    return books

@book_router.get('/user-books', response_model=List[BookModel], dependencies=[role_checker])
async def get_user_books(session: AsyncSession = Depends(get_session), 
                        token_details: dict = Depends(jwt_bearer)):
    user_uid = token_details.get('user')['user_uid']
    books = await book_service.get_user_books(user_uid, session)
    return books

@book_router.post('/', status_code=status.HTTP_201_CREATED, response_model=BookModel, dependencies=[role_checker])
async def create_a_book(book_data: BookCreateModel, 
                        session: AsyncSession = Depends(get_session), 
                        token_details: dict =Depends(jwt_bearer)) -> dict:
    user_id = token_details.get('user')['user_uid']
    new_book = await book_service.create_books(book_data, user_id, session)
    return new_book


@book_router.get('/{book_uid}',response_model= BookDetailModel, dependencies=[role_checker])
async def get_book(book_uid: uuid.UUID, session: AsyncSession = Depends(get_session), token_details: dict =Depends(jwt_bearer)) -> dict:
    book = await book_service.get_book_id(book_uid, session)
    if book:
        return book
    else:
        raise BookNotFound()


@book_router.patch('/{book_uid}', dependencies=[role_checker])
async def update_book(book_uid: uuid.UUID, book_update_data: BookUpdateModel, session: AsyncSession = Depends(get_session), token_details: dict =Depends(jwt_bearer)) -> dict:
    updated_book = await book_service.update_book(book_uid, book_update_data, session)

    if updated_book:
        return updated_book
    else:
        raise BookNotFound()


@book_router.delete('/{book_uid}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[role_checker])
async def delete_book(book_uid: uuid.UUID, session: AsyncSession = Depends(get_session), token_details: dict =Depends(jwt_bearer)):
    book_to_delete = await book_service.delete_book(book_uid, session)

    if book_to_delete:
        return {}
    else:
        raise BookNotFound()
