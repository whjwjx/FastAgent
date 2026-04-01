from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import TypeDecorator, JSON
from database.session import Base
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector

class StringArray(TypeDecorator):
    """
    Use PostgreSQL ARRAY when using PostgreSQL,
    and use JSON when using SQLite (for testing).
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String()))
        else:
            return dialect.type_descriptor(JSON())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    thoughts = relationship("Thought", back_populates="owner")
    schedules = relationship("Schedule", back_populates="owner")
    garden_config = relationship("GardenConfig", back_populates="owner", uselist=False)

class GardenConfig(Base):
    __tablename__ = "garden_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    theme = Column(Integer, default=1) # 1=简约风, 2=时间线风, 3=花园卡片风
    slug = Column(String, unique=True, index=True, nullable=True)
    share_token = Column(String, unique=True, index=True, nullable=True)
    is_share_open = Column(Boolean, default=False, index=True)
    custom_domain = Column(String, unique=True, index=True, nullable=True)
    custom_html = Column(Text, nullable=True)
    custom_css = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    owner = relationship("User", back_populates="garden_config")

class Thought(Base):
    __tablename__ = "thoughts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    original_content = Column(Text, nullable=False)
    refined_content = Column(Text, nullable=True)
    tags = Column(StringArray, nullable=True)  # Store as PostgreSQL ARRAY or JSON
    thought_type = Column(String, default="idea", index=True) # idea, blog, weekly_report, etc.
    source_ids = Column(StringArray, nullable=True) # Store source thought IDs as strings
    is_public = Column(Boolean, default=False, index=True)
    embedding = Column(Vector(2048), nullable=True) # Doubao multimodal embedding is 2048 dims
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False, index=True)
    
    owner = relationship("User", back_populates="thoughts")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    status = Column(String, default="待办", index=True) # 待办/已完成/已过期
    reminder_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False, index=True)
    
    owner = relationship("User", back_populates="schedules")
