from typing import Optional

from pydantic import BaseModel, Json, EmailStr


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    external_data: Optional[Json] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class LikeBase(BaseModel):
    user_id: int
    post_id: int


class Like(LikeBase):
    id: int

    class Config:
        orm_mode = True
