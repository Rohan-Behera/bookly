from .models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schemas import UserCreateModel


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        res = await session.exec(statement)
        user = res.first()
        return user
    
    async def user_exists(self, email, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return True if user else False
    
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user = user_data
        new_user = User(
            **user_data
        )