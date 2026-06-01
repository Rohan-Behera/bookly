from src.db.models import Reviews
from src.auth.service import UserService
from src.books.service import BookService
from sqlmodel.ext.asyncio.session import AsyncSession


class ReviewService:
    async def add_review_to_book(user_uid: str, book_uid: str, session: AsyncSession):
        pass