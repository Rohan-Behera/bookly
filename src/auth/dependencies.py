from fastapi import Request, status, Depends
from fastapi.security import HTTPBearer
from .utils import decode_token
from fastapi.exceptions import HTTPException
from src.db.redis import token_in_blocklist
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import UserService
from typing import List
from .models import User

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or token expired")

        if await token_in_blocklist(token_data['jti']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail={
                    "error": "This token is Invalid or has been Revoked",
                    "resolution": "Please get a new token"
                })
        
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an access token")
        
class RefreshTokenBearer(JWTBearer):
    def verify_token_data(self, token_data):
        if token_data and not token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide a refresh token")
        
async def get_current_user(token_details: dict = Depends(AccessTokenBearer()), 
                     session: AsyncSession = Depends(get_session)):
    user_email = token_details['user']['email']
    user = await user_service.get_user_by_email(user_email, session)

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role in self.allowed_roles:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")