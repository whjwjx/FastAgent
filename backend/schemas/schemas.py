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
    original_content: str
    refined_content: Optional[str] = None
    tags: Optional[List[str]] = None

class ThoughtUpdate(BaseModel):
    original_content: Optional[str] = None
    refined_content: Optional[str] = None
    tags: Optional[List[str]] = None

class ThoughtResponse(ThoughtCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ScheduleCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = "待办"
    reminder_time: Optional[datetime] = None

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None
    reminder_time: Optional[datetime] = None

class ScheduleResponse(ScheduleCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
