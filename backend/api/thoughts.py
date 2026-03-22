from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.session import get_db
from models.models import Thought, User
from schemas.schemas import ThoughtCreate, ThoughtResponse
from api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=ThoughtResponse)
def create_thought(thought: ThoughtCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_thought = Thought(**thought.model_dump(), user_id=current_user.id)
    db.add(db_thought)
    db.commit()
    db.refresh(db_thought)
    return db_thought

@router.get("/", response_model=List[ThoughtResponse])
def get_thoughts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Thought).filter(Thought.user_id == current_user.id).order_by(Thought.created_at.desc()).all()
