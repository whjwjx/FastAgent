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

class ThoughtBase(BaseModel):
    original_content: str
    refined_content: Optional[str] = None
    tags: Optional[List[str]] = []
    thought_type: Optional[str] = "idea"
    source_ids: Optional[List[str]] = None
    is_public: Optional[bool] = False

class ThoughtCreate(ThoughtBase):
    pass

class ThoughtUpdate(BaseModel):
    original_content: Optional[str] = None
    refined_content: Optional[str] = None
    tags: Optional[List[str]] = None
    thought_type: Optional[str] = None
    source_ids: Optional[List[str]] = None
    is_public: Optional[bool] = None

class ThoughtResponse(ThoughtBase):
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

class GardenConfigBase(BaseModel):
    theme: Optional[int] = 1
    slug: Optional[str] = None
    share_token: Optional[str] = None
    is_share_open: Optional[bool] = False
    custom_domain: Optional[str] = None
    custom_html: Optional[str] = None
    custom_css: Optional[str] = None

class GardenConfigUpdate(GardenConfigBase):
    pass

class GardenConfigResponse(GardenConfigBase):
    id: int
    user_id: int
    updated_at: datetime
    class Config:
        from_attributes = True

class SharedGardenResponse(BaseModel):
    owner_nickname: str
    owner_avatar: Optional[str] = None
    owner_bio: Optional[str] = None
    config: GardenConfigResponse
    thoughts: List[ThoughtResponse]
