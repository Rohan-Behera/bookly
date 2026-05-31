from fastapi import Request, status
from fastapi.security import HTTPBearer
from .utils import decode_token
from fastapi.exceptions import HTTPException

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