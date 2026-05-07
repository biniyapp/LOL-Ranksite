from pydantic import BaseModel

class UserBase(BaseModel):
    nickname: str
    tag: str
    score: int

class UserCreate(BaseModel):
    nickname: str
    tag: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True
