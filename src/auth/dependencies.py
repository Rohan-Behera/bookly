from fastapi import Request, status, Depends
from fastapi.security import HTTPBearer
from .utils import decode_token
from fastapi.exceptions import HTTPException
from src.db.redis import token_in_blocklist
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import UserService
from typing import List
from src.db.models import User
from src.errors import InvalidToken, RefreshTokenRequired, AccessTokenRequired, InsufficientPermission, AccountNotVerified

user_service = UserService()

# overwriting the basse HTTPBearer methods to our own methods
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        cred = await super().__call__(request)
        token = cred.credentials

        token_data = decode_token(token)

        if not self.token_is_valid(token):
            raise InvalidToken()

        if await token_in_blocklist(token_data['jti']):
            raise InvalidToken()
        
        self.verify_token_data(token_data)
        return token_data

    def token_is_valid(self, token: str) -> bool:
        token_data = decode_token(token)

        return True if token_data else False
    
    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")


class AccessTokenBearer(JWTBearer):
    def verify_token_data(self, token_data):
        if token_data and token_data['refresh']:
            raise AccessTokenRequired()
        
class RefreshTokenBearer(JWTBearer):
    def verify_token_data(self, token_data):
        if token_data and not token_data['refresh']:
            raise RefreshTokenRequired()
        
async def get_current_user(token_details: dict = Depends(AccessTokenBearer()), 
                     session: AsyncSession = Depends(get_session)):
    user_email = token_details['user']['email']
    user = await user_service.get_user_by_email(user_email, session)

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True
        else:
            raise InsufficientPermission()