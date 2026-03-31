from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from database.session import get_db
from models.models import GardenConfig, Thought, User
from schemas.schemas import GardenConfigResponse, GardenConfigUpdate, SharedGardenResponse, ThoughtResponse
from api.deps import get_current_user

router = APIRouter()

def get_or_create_garden_config(db: Session, user_id: int) -> GardenConfig:
    config = db.query(GardenConfig).filter(GardenConfig.user_id == user_id).first()
    if not config:
        # Generate a default slug based on username if possible, or just a UUID
        user = db.query(User).filter(User.id == user_id).first()
        default_slug = user.username if user else str(uuid.uuid4())[:8]
        
        # Ensure slug uniqueness
        existing_slug = db.query(GardenConfig).filter(GardenConfig.slug == default_slug).first()
        if existing_slug:
            default_slug = f"{default_slug}-{str(uuid.uuid4())[:4]}"

        config = GardenConfig(
            user_id=user_id,
            share_token=str(uuid.uuid4()),
            slug=default_slug,
            is_share_open=False,
            theme=1
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.get("/config", response_model=GardenConfigResponse)
def get_my_garden_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_or_create_garden_config(db, current_user.id)

@router.put("/config", response_model=GardenConfigResponse)
def update_my_garden_config(
    config_update: GardenConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = get_or_create_garden_config(db, current_user.id)
    
    update_data = config_update.model_dump(exclude_unset=True)
    
    # Check slug uniqueness if it's being updated
    if "slug" in update_data and update_data["slug"] != db_config.slug:
        existing = db.query(GardenConfig).filter(GardenConfig.slug == update_data["slug"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already taken")
            
    # If share_token is requested to be reset (e.g. by passing a special value or just handling it here)
    # For now, let's assume we might have a separate reset endpoint or just handle it if it's in the update
    
    for key, value in update_data.items():
        setattr(db_config, key, value)
        
    db.commit()
    db.refresh(db_config)
    return db_config

@router.post("/config/reset-token", response_model=GardenConfigResponse)
def reset_share_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_config = get_or_create_garden_config(db, current_user.id)
    db_config.share_token = str(uuid.uuid4())
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/shared/token/{token}", response_model=SharedGardenResponse)
def get_shared_garden_by_token(token: str, db: Session = Depends(get_db)):
    config = db.query(GardenConfig).filter(GardenConfig.share_token == token).first()
    if not config or not config.is_share_open:
        raise HTTPException(status_code=404, detail="Garden not found or sharing is disabled")
        
    return _get_shared_content(db, config)

@router.get("/shared/slug/{slug}", response_model=SharedGardenResponse)
def get_shared_garden_by_slug(slug: str, db: Session = Depends(get_db)):
    config = db.query(GardenConfig).filter(GardenConfig.slug == slug).first()
    if not config or not config.is_share_open:
        raise HTTPException(status_code=404, detail="Garden not found or sharing is disabled")
        
    return _get_shared_content(db, config)

def _get_shared_content(db: Session, config: GardenConfig) -> dict:
    # Get the owner's basic info
    owner = config.owner
    
    # Get only public thoughts
    public_thoughts = db.query(Thought).filter(
        Thought.user_id == owner.id,
        Thought.is_public == True,
        Thought.is_deleted == False
    ).order_by(Thought.created_at.desc()).all()
    
    return {
        "owner_nickname": owner.username, # In a real app, we might have a separate nickname field
        "owner_avatar": None,
        "owner_bio": None,
        "config": config,
        "thoughts": public_thoughts
    }
