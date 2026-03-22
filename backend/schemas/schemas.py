from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ThoughtCreate(BaseModel):
    content: str

class ThoughtResponse(ThoughtCreate):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ScheduleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class ScheduleResponse(ScheduleCreate):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True
