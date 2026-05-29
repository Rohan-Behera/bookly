from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class UserCreateModel(BaseModel):
    username: str = Field(max_length = 8)
    email: str = Field(max_length = 40)
    password: str = Field(min_length = 8)
    first_name: str
    last_name: str

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
