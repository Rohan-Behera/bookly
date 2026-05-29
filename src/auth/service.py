from .models import User
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .schemas import UserCreateModel
from .utils import generate_password_hash


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
        user = user_data.model_dump()
        new_user = User(
            **user
        )
        new_user.password = generate_password_hash(user['password'])

        session.add(new_user)
        await session.commit()
        session.refresh(new_user)
        return new_user