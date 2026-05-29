from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import BookCreateModel
from sqlmodel import select, desc
from .models import Book

class BookService:
    async def get_all_books(self, session:AsyncSession):
        statement = select(Book).order_by(desc(Book.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_book_id(self, book_uid:str, session:AsyncSession):
        statement = select(Book).where(Book.uid == book_uid)

        result = await session.exec(statement)
        book = result.first()

        return book if book is not None else None

    async def create_books(self, book_data: BookCreateModel, session:AsyncSession):
        book_data_dict = book_data.model_dump()
        new_book = Book(
            **book_data_dict
        )
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book

    async def update_book(self, book_uid: int, updated_data: BookCreateModel, session:AsyncSession):
        book_to_update = await self.get_book_id(book_uid, session)

        if book_to_update is not None:
            update_data_dict = updated_data.model_dump(exclude_unset=True) #only updates provided fields

            for k, v in update_data_dict.items():
                setattr(book_to_update, k, v)
            
            await session.commit()
            await session.refresh(book_to_update)
            return book_to_update
        else:
            return None

    async def delete_book(self, book_uid: int, session:AsyncSession):
        book_to_delete = self.get_book_id(book_uid, session)

        if book_to_delete is not None:
            await session.delete(book_to_delete)

            await session.commit()
        else:
            return None