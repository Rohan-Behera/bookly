from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import List
from src.books.schemas import BookModel
from src.reviews.schemas import ReviewModel


class UserCreateModel(BaseModel):
    first_name: str
    last_name: str
    username: str = Field(max_length = 8)
    email: str = Field(max_length = 40)
    password: str = Field(min_length = 8)   

class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    password: str = Field(exclude=True) #excludes the password to be returned in response
    email:str
    first_name: str
    last_name: str
    is_verified: bool 
    created_at: datetime
    updated_at: datetime

class UserBooksModel(UserModel):
    books: List[BookModel]
    reviews: List[ReviewModel]

class UserLoginModel(BaseModel):
    email: str = Field(max_length = 40)
    password: str = Field(min_length = 8)

class EmailModel(BaseModel):
    addresses: List[str]

class PasswordRequestModel(BaseModel):
    email: str

class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_password: str