from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.session import get_db
from models.models import Thought, User
from schemas.schemas import ThoughtCreate, ThoughtUpdate, ThoughtResponse
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
def get_thoughts(
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Thought).filter(Thought.user_id == current_user.id, Thought.is_deleted == False)
    if keyword:
        query = query.filter(
            (Thought.original_content.ilike(f"%{keyword}%")) | 
            (Thought.refined_content.ilike(f"%{keyword}%"))
        )
    if tag:
        query = query.filter(Thought.tags.any(tag))
        
    return query.order_by(Thought.created_at.desc()).all()

@router.put("/{thought_id}", response_model=ThoughtResponse)
def update_thought(
    thought_id: int, 
    thought_update: ThoughtUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_thought = db.query(Thought).filter(Thought.id == thought_id, Thought.user_id == current_user.id, Thought.is_deleted == False).first()
    if not db_thought:
        raise HTTPException(status_code=404, detail="Thought not found")
        
    update_data = thought_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_thought, key, value)
        
    db.commit()
    db.refresh(db_thought)
    return db_thought

@router.delete("/{thought_id}")
def delete_thought(thought_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_thought = db.query(Thought).filter(Thought.id == thought_id, Thought.user_id == current_user.id, Thought.is_deleted == False).first()
    if not db_thought:
        raise HTTPException(status_code=404, detail="Thought not found")
        
    db_thought.is_deleted = True
    db.commit()
    return {"message": "Thought deleted successfully"}

@router.delete("/")
def clear_thoughts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Thought).filter(Thought.user_id == current_user.id, Thought.is_deleted == False).update({"is_deleted": True})
    db.commit()
    return {"message": "All thoughts cleared successfully"}
