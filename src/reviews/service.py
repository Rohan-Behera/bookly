from src.db.models import Reviews
from src.auth.service import UserService
from src.books.service import BookService
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import ReviewCreateModel
from fastapi.exceptions import HTTPException
from fastapi import status


book_service = BookService()
User_service = UserService()
class ReviewService:
    async def add_review_to_book(self, user_email: str, book_uid: str, review_data: ReviewCreateModel ,session: AsyncSession):
        try:
            book = await book_service.get_book_id(book_uid, session)
            user = await User_service.get_user_by_email(email=user_email, session=session)
            new_review=Reviews(**review_data.model_dump())

            if not book:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
            
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found ")

            new_review.user = user
            new_review.books = book
            
            session.add(new_review)
            await session.commit()
            await session.refresh(new_review)

            return new_review
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Oops something went wrong....{str(e)}"
            )